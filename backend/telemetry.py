"""Telemetry bus (PRD §4.6).

Every pipeline stage emits a structured event here. Events fan out to (a) live
WebSocket subscribers for the visualizer and (b) a per-run JSONL log that
eval/run_eval.py consumes. One emitter, two sinks — the demo numbers and the
report numbers are physically the same data.
"""
from __future__ import annotations

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional

from . import config

Subscriber = Callable[[dict[str, Any]], Awaitable[None]]


class TelemetryBus:
    def __init__(self, session_id: str, run_log_dir: Path | None = None) -> None:
        self.session_id = session_id
        self.run_id = uuid.uuid4().hex[:8]
        self.events: list[dict[str, Any]] = []
        self._subscribers: list[Subscriber] = []
        self._t0 = time.perf_counter()
        self._log_dir = Path(run_log_dir or config.RUNLOG_DIR)
        self._log_path: Optional[Path] = None
        self._lock = asyncio.Lock()

    # ---------- timing ----------

    def reset_clock(self) -> None:
        self._t0 = time.perf_counter()

    @property
    def elapsed_s(self) -> float:
        return time.perf_counter() - self._t0

    # ---------- subscribers ----------

    def subscribe(self, fn: Subscriber) -> None:
        self._subscribers.append(fn)

    def unsubscribe(self, fn: Subscriber) -> None:
        if fn in self._subscribers:
            self._subscribers.remove(fn)

    # ---------- emit ----------

    def _build(self, event: str, **fields: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "event": event,
            "session_id": self.session_id,
            "run_id": self.run_id,
            "timestamp_s": round(self.elapsed_s, 4),
            "wall_time": time.time(),
        }
        payload.update(fields)
        return payload

    async def emit(self, event: str, **fields: Any) -> dict[str, Any]:
        payload = self._build(event, **fields)
        self.events.append(payload)
        # A dead/slow client must never break the pipeline.
        for sub in list(self._subscribers):
            try:
                await sub(payload)
            except Exception:  # noqa: BLE001
                self.unsubscribe(sub)
        return payload

    def emit_sync(self, event: str, **fields: Any) -> dict[str, Any]:
        """For non-async call sites (eval harness). Skips live subscribers."""
        payload = self._build(event, **fields)
        self.events.append(payload)
        return payload

    # ---------- persistence ----------

    def log_path(self) -> Path:
        if self._log_path is None:
            self._log_dir.mkdir(parents=True, exist_ok=True)
            self._log_path = self._log_dir / f"run_{self.session_id}_{self.run_id}.jsonl"
        return self._log_path

    def flush(self) -> Path:
        path = self.log_path()
        with path.open("w", encoding="utf-8") as fh:
            for ev in self.events:
                fh.write(json.dumps(ev, ensure_ascii=False) + "\n")
        return path

    def events_of(self, event_name: str) -> list[dict[str, Any]]:
        return [e for e in self.events if e.get("event") == event_name]
