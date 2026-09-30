"""Session-bound state (architecture.md §4).

Hard constraint from the brief: nothing is ever keyed by user identity and
nothing survives the session. Both backends enforce that structurally — the
only key shape is `session:{session_id}:answer_state`, always with a TTL.

Redis is used when AEGIS_REDIS_URL is set; otherwise an in-process TTL dict.
The memory backend is not a downgrade for this workload: a single-process demo
has exactly one reader and one writer.
"""
from __future__ import annotations

import time
from typing import Optional, Protocol

from . import config
from .schemas import AnswerState


def _key(session_id: str) -> str:
    return f"session:{session_id}:answer_state"


class SessionBackend(Protocol):
    async def get(self, session_id: str) -> Optional[AnswerState]: ...
    async def set(self, state: AnswerState) -> None: ...
    async def delete(self, session_id: str) -> None: ...


class MemorySessionStore:
    backend_name = "memory"

    def __init__(self, ttl_s: int | None = None) -> None:
        self.ttl_s = ttl_s or config.SESSION_TTL_S
        self._data: dict[str, tuple[float, str]] = {}

    def _purge(self) -> None:
        now = time.time()
        for k in [k for k, (exp, _) in self._data.items() if exp <= now]:
            self._data.pop(k, None)

    async def get(self, session_id: str) -> Optional[AnswerState]:
        self._purge()
        entry = self._data.get(_key(session_id))
        if entry is None:
            return None
        try:
            return AnswerState.model_validate_json(entry[1])
        except Exception:  # noqa: BLE001 - corrupt entry is treated as absent
            self._data.pop(_key(session_id), None)
            return None

    async def set(self, state: AnswerState) -> None:
        self._purge()
        self._data[_key(state.session_id)] = (
            time.time() + self.ttl_s,
            state.model_dump_json(),
        )

    async def delete(self, session_id: str) -> None:
        self._data.pop(_key(session_id), None)


class RedisSessionStore:
    backend_name = "redis"

    def __init__(self, url: str, ttl_s: int | None = None) -> None:
        import redis.asyncio as redis  # noqa: PLC0415

        self.ttl_s = ttl_s or config.SESSION_TTL_S
        self._redis = redis.from_url(url, decode_responses=True)

    async def get(self, session_id: str) -> Optional[AnswerState]:
        raw = await self._redis.get(_key(session_id))
        if not raw:
            return None
        try:
            return AnswerState.model_validate_json(raw)
        except Exception:  # noqa: BLE001
            return None

    async def set(self, state: AnswerState) -> None:
        await self._redis.set(
            _key(state.session_id), state.model_dump_json(), ex=self.ttl_s
        )

    async def delete(self, session_id: str) -> None:
        await self._redis.delete(_key(session_id))


_store: Optional[SessionBackend] = None


def get_store() -> SessionBackend:
    """Redis when configured and importable, memory otherwise. Falling back is
    always safe here because the store is explicitly ephemeral by design."""
    global _store
    if _store is not None:
        return _store
    if config.REDIS_URL:
        try:
            _store = RedisSessionStore(config.REDIS_URL)
            return _store
        except Exception:  # noqa: BLE001
            pass
    _store = MemorySessionStore()
    return _store


def set_store(store: Optional[SessionBackend]) -> None:
    global _store
    _store = store
