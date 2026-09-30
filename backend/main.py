"""Streaming gateway: FastAPI + WebSocket.

Endpoints
  GET  /                 -> the visualizer UI
  GET  /api/health       -> readiness + which backends are actually live
  GET  /api/corpus       -> chunk inventory (used by the citation hover card)
  POST /api/turn         -> run one turn synchronously (used by tests/eval)
  POST /api/race         -> naive vs Aegis on the same utterance (PRD §2.1 C)
  WS   /ws/{session_id}  -> live chunked ingestion + telemetry + token stream
"""
from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import config
from .embeddings import get_encoder
from .llm import get_client
from .pipeline import AegisPipeline, LiveTurn, TranscriptChunk
from .retrieval.engine import get_engine
from .session_store import get_store
from .telemetry import TelemetryBus

FRONTEND_DIR = config.ROOT / "frontend"

app = FastAPI(title="Aegis — Streaming Live RAG", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_pipeline: Optional[AegisPipeline] = None


def pipeline() -> AegisPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = AegisPipeline()
    return _pipeline


@app.on_event("startup")
async def _startup() -> None:
    # Warm the index and encoder off the request path so the first demo turn is
    # not paying a cold-start cost the metrics would unfairly attribute to TTFT.
    await asyncio.to_thread(get_engine)
    await asyncio.to_thread(get_encoder)
    pipeline()


# ---------------- models ----------------

class TurnRequest(BaseModel):
    session_id: str = Field(default="demo")
    utterance: str
    chunk_ms: int = 300
    system: str = "aegis"  # aegis | naive


class RaceRequest(BaseModel):
    session_id: str = Field(default="race")
    utterance: str
    chunk_ms: int = 300


# ---------------- helpers ----------------

def simulate_chunks(utterance: str, chunk_ms: int = 300) -> list[TranscriptChunk]:
    """Split an utterance into timestamped word groups, as a live ASR would."""
    words = (utterance or "").split()
    if not words:
        return [TranscriptChunk(t=0.0, text="", is_final=True)]
    group = 3
    chunks: list[TranscriptChunk] = []
    t = 0.0
    for i in range(0, len(words), group):
        piece = " ".join(words[i:i + group])
        t = round(i / group * (chunk_ms / 1000.0), 3)
        chunks.append(TranscriptChunk(t=t, text=piece))
    chunks[-1].is_final = True
    chunks[-1].silence_s = config.SILENCE_TIMEOUT_S
    return chunks


# ---------------- REST ----------------

@app.get("/api/health")
async def health() -> dict[str, Any]:
    engine = get_engine()
    client = get_client()
    store = get_store()
    return {
        "status": "ok",
        "chunks_indexed": len(engine.chunks),
        "documents": len({c.doc_id for c in engine.chunks}),
        "embedding_backend": getattr(get_encoder(), "name", "unknown"),
        "llm_provider": client.provider,
        "session_backend": getattr(store, "backend_name", "unknown"),
        "ablations": {
            "use_sparse": config.USE_SPARSE,
            "use_dense": config.USE_DENSE,
            "use_reranker": config.USE_RERANKER,
            "controller_mode": config.CONTROLLER_MODE,
        },
    }


@app.get("/api/corpus")
async def corpus() -> dict[str, Any]:
    engine = get_engine()
    return {
        "count": len(engine.chunks),
        "chunks": [
            {
                "chunk_id": c.chunk_id,
                "doc_id": c.doc_id,
                "section": c.section,
                "citation": c.citation,
                "text": c.text,
            }
            for c in engine.chunks
        ],
    }


@app.post("/api/turn")
async def run_turn(req: TurnRequest) -> JSONResponse:
    if not req.utterance.strip():
        raise HTTPException(status_code=400, detail="utterance must not be empty")
    bus = TelemetryBus(req.session_id)
    chunks = simulate_chunks(req.utterance, req.chunk_ms)
    if req.system == "naive":
        from eval.baseline_naive_rag import NaivePipeline  # noqa: PLC0415

        result = await NaivePipeline().run_turn(req.session_id, chunks, bus)
    else:
        result = await pipeline().run_turn(req.session_id, chunks, bus)
    return JSONResponse(
        {"result": result.model_dump(), "events": bus.events}
    )


@app.post("/api/race")
async def race(req: RaceRequest) -> JSONResponse:
    """Naive vs Aegis on the same utterance — the Live Race (PRD §2.1 C).

    Calls exactly the same pipeline objects the offline eval calls; there is no
    separate demo-only code path.
    """
    from eval.baseline_naive_rag import NaivePipeline  # noqa: PLC0415

    if not req.utterance.strip():
        raise HTTPException(status_code=400, detail="utterance must not be empty")
    chunks = simulate_chunks(req.utterance, req.chunk_ms)
    aegis_bus = TelemetryBus(f"{req.session_id}_aegis")
    naive_bus = TelemetryBus(f"{req.session_id}_naive")

    aegis_task = asyncio.create_task(
        pipeline().run_turn(f"{req.session_id}_aegis", chunks, aegis_bus)
    )
    naive_task = asyncio.create_task(
        NaivePipeline().run_turn(f"{req.session_id}_naive", chunks, naive_bus)
    )
    aegis_result, naive_result = await asyncio.gather(aegis_task, naive_task)
    return JSONResponse(
        {
            "aegis": {"result": aegis_result.model_dump(), "events": aegis_bus.events},
            "naive": {"result": naive_result.model_dump(), "events": naive_bus.events},
            "delta": {
                "ttft_ms_saved": round(
                    naive_result.metrics.ttft_ms - aegis_result.metrics.ttft_ms, 2
                ),
                "aegis_sub_queries": len(aegis_result.sub_queries),
                "naive_sub_queries": len(naive_result.sub_queries),
            },
        }
    )


@app.post("/api/session/{session_id}/reset")
async def reset_session(session_id: str) -> dict[str, str]:
    await get_store().delete(session_id)
    return {"status": "reset", "session_id": session_id}


# ---------------- WebSocket ----------------

@app.websocket("/ws/{session_id}")
async def ws_endpoint(websocket: WebSocket, session_id: str) -> None:
    """Bi-directional chunked ingestion.

    Client → server messages:
      {"type":"chunk","text":"...","t":0.8}      incremental transcript chunk
      {"type":"end"}                             utterance finished
      {"type":"utterance","text":"...","chunk_ms":300}   simulate a full turn
      {"type":"barge_in","text":"..."}           interruption (PRD §2.1 A)
      {"type":"reset"}                           clear session state
    """
    await websocket.accept()
    bus = TelemetryBus(session_id)
    live_turn: LiveTurn | None = None
    lock = asyncio.Lock()

    async def send(payload: dict[str, Any]) -> None:
        await websocket.send_json(payload)

    bus.subscribe(send)

    async def on_token(token: str) -> None:
        await websocket.send_json({"event": "token", "text": token})

    async def execute(chunks: list[TranscriptChunk]) -> None:
        async with lock:  # one turn at a time per socket
            try:
                result = await pipeline().run_turn(
                    session_id, chunks, bus, on_token=on_token
                )
                await websocket.send_json(
                    {"event": "turn_result", "result": result.model_dump()}
                )
                await asyncio.to_thread(bus.flush)
            except Exception as exc:  # noqa: BLE001 - report, keep socket alive
                await websocket.send_json({"event": "error", "detail": str(exc)})

    try:
        await send(await health())
        while True:
            msg = await websocket.receive_json()
            mtype = msg.get("type")

            if mtype == "chunk":
                if live_turn is None or live_turn.finished:
                    live_turn = await pipeline().begin_live_turn(session_id, bus, on_token=on_token)
                await pipeline().ingest_live_chunk(
                    live_turn,
                    TranscriptChunk(
                        t=float(msg.get("t", bus.elapsed_s)),
                        text=str(msg.get("text", "")),
                    ),
                )
            elif mtype == "replace":
                if live_turn is None or live_turn.finished:
                    live_turn = await pipeline().begin_live_turn(session_id, bus, on_token=on_token)
                await pipeline().replace_live_text(
                    live_turn, str(msg.get("text", "")), float(msg.get("t", bus.elapsed_s))
                )
            elif mtype == "end":
                if live_turn is not None and not live_turn.finished:
                    async with lock:
                        result = await pipeline().finish_live_turn(live_turn)
                        await websocket.send_json({"event": "turn_result", "result": result.model_dump()})
                        await asyncio.to_thread(bus.flush)
                    live_turn = None
            elif mtype in {"utterance", "barge_in"}:
                text = str(msg.get("text", "")).strip()
                if text:
                    await execute(
                        simulate_chunks(text, int(msg.get("chunk_ms", 300)))
                    )
            elif mtype == "reset":
                await get_store().delete(session_id)
                if live_turn and live_turn.ctx.provisional_task and not live_turn.ctx.provisional_task.done():
                    live_turn.ctx.provisional_task.cancel()
                live_turn = None
                await websocket.send_json({"event": "session_reset"})
            elif mtype == "ping":
                await websocket.send_json({"event": "pong"})
    except WebSocketDisconnect:
        pass
    except Exception:  # noqa: BLE001
        with contextlib.suppress(Exception):
            await websocket.close()
    finally:
        bus.unsubscribe(send)


# ---------------- static frontend (mounted last) ----------------

if FRONTEND_DIR.exists():
    app.mount(
        "/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static"
    )

    @app.get("/")
    async def index() -> FileResponse:
        html = FRONTEND_DIR / "index.html"
        if not html.exists():
            raise HTTPException(status_code=404, detail="frontend/index.html missing")
        return FileResponse(str(html))
