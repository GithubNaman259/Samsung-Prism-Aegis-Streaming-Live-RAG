"""LLM provider abstraction.

Two providers:
  * "anthropic" — used automatically when ANTHROPIC_API_KEY is present.
  * "ollama" — a local, free/open-source model server (default when available).
  * "heuristic" — a deterministic, offline stub used otherwise.

The stub is not decoration: it means `git clone && docker compose up` produces a
fully working demo with zero credentials, and it makes every eval run
reproducible bit-for-bit. Each call site (decomposer, suppression, synthesis,
grounding) has a heuristic path, so no stage silently degrades to nothing.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Optional

from . import config


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def add(self, other: "Usage") -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.calls += other.calls

    def cost_usd(self) -> float:
        return (
            self.input_tokens / 1000.0 * config.USD_PER_1K_INPUT_TOKENS
            + self.output_tokens / 1000.0 * config.USD_PER_1K_OUTPUT_TOKENS
        )


@dataclass
class LLMResponse:
    text: str
    usage: Usage = field(default_factory=Usage)


def estimate_tokens(text: str) -> int:
    """~4 chars/token. Used for the stub and as a fallback when the provider
    does not return usage. Deliberately provider-agnostic."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def extract_json(text: str) -> Optional[Any]:
    """Tolerant JSON extraction: handles ```json fences and surrounding prose."""
    if not text:
        return None
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    for opener, closer in (("{", "}"), ("[", "]")):
        start = cleaned.find(opener)
        end = cleaned.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                continue
    return None


class LLMClient:
    """Thin async wrapper. Never raises to callers — on any provider error it
    returns an empty response and the caller falls back to its heuristic path."""

    def __init__(self, provider: Optional[str] = None) -> None:
        requested = (provider or config.LLM_PROVIDER).lower()
        key = config.ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY", "")
        self._api_key = key
        self._client = None
        self.ollama_url = os.getenv("AEGIS_OLLAMA_URL", "http://127.0.0.1:11434")
        self.ollama_model = "llama3.1:8b"
        if requested == "ollama":
            self.provider = "ollama"
        elif requested == "anthropic" and key:
            self.provider = "anthropic"
        elif requested == "anthropic":
            self.provider = "heuristic"
        elif requested == "heuristic":
            self.provider = "heuristic"
        else:
            # Auto prefers a local model when Ollama is reachable, then falls
            # back to Anthropic, then to the deterministic implementation.
            self.provider = (
                "ollama"
                if self._ollama_available()
                else ("anthropic" if key else "heuristic")
            )

    @property
    def is_stub(self) -> bool:
        return self.provider == "heuristic"

    def _ollama_available(self) -> bool:
        try:
            req = urllib.request.Request(
                f"{self.ollama_url.rstrip('/')}/api/tags", method="GET"
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                if not (200 <= resp.status < 300):
                    return False
                payload = json.loads(resp.read().decode("utf-8"))
                names = {
                    str(x.get("name", ""))
                    for x in payload.get("models", [])
                    if isinstance(x, dict)
                }
                return self.ollama_model in names
        except Exception:
            return False

    async def _ollama(
        self, system: str, prompt: str, max_tokens: int, *, json_mode: bool = False
    ) -> LLMResponse:
        payload = {
            "model": self.ollama_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "think": False,
            "options": {"temperature": 0.1, "num_predict": max_tokens},
        }
        if json_mode:
            payload["format"] = "json"
        data = json.dumps(payload).encode("utf-8")

        def call() -> LLMResponse:
            req = urllib.request.Request(
                f"{self.ollama_url.rstrip('/')}/api/chat",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=config.LLM_TIMEOUT_S) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
                text = str(body.get("message", {}).get("content", ""))
                usage = Usage(
                    input_tokens=int(
                        body.get("prompt_eval_count") or estimate_tokens(prompt)
                    ),
                    output_tokens=int(body.get("eval_count") or estimate_tokens(text)),
                    calls=1,
                )
                return LLMResponse(text, usage)
            except Exception as exc:
                print(f"[Ollama ERROR] {type(exc).__name__}: {exc}")
                return LLMResponse("", Usage(calls=1))

        return await asyncio.to_thread(call)

    async def _anthropic(
        self, system: str, prompt: str, max_tokens: int
    ) -> LLMResponse:
        try:
            import anthropic  # noqa: PLC0415
        except ImportError:
            self.provider = "heuristic"
            return LLMResponse("", Usage())
        if self._client is None:
            self._client = anthropic.AsyncAnthropic(
                api_key=self._api_key, timeout=config.LLM_TIMEOUT_S
            )
        try:
            msg = await self._client.messages.create(
                model=config.LLM_MODEL,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception:  # noqa: BLE001 - degrade, never crash the turn
            return LLMResponse("", Usage(calls=1))
        text = "".join(
            block.text for block in msg.content if getattr(block, "type", "") == "text"
        )
        usage = Usage(
            input_tokens=getattr(msg.usage, "input_tokens", 0),
            output_tokens=getattr(msg.usage, "output_tokens", 0),
            calls=1,
        )
        return LLMResponse(text, usage)

    async def complete(
        self, system: str, prompt: str, max_tokens: int = 700
    ) -> LLMResponse:
        if self.provider == "ollama":
            resp = await self._ollama(system, prompt, max_tokens, json_mode=False)
            if resp.text:
                return resp
            return resp
        if self.provider == "anthropic":
            resp = await self._anthropic(system, prompt, max_tokens)
            return resp
        return LLMResponse("", Usage())

    async def complete_json(
        self, system: str, prompt: str, max_tokens: int = 700
    ) -> tuple[Optional[Any], Usage]:
        if self.provider == "ollama":
            resp = await self._ollama(system, prompt, max_tokens, json_mode=True)
        else:
            resp = await self.complete(system, prompt, max_tokens)
        return extract_json(resp.text), resp.usage


_shared: Optional[LLMClient] = None


def get_client() -> LLMClient:
    global _shared
    if _shared is None:
        _shared = LLMClient()
    return _shared


def reset_client() -> None:
    global _shared
    _shared = None
