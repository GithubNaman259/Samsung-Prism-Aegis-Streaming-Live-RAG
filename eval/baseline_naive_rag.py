"""Naive RAG baseline — the control arm for every comparison.

Deliberately built from the *same* retrieval engine and the *same* synthesis
function as Aegis, with exactly four differences, so any measured delta is
attributable to the four required behaviours and nothing else:

  1. No streaming controller — it waits for the full utterance (no speculation).
  2. No decomposition — one query, the raw utterance.
  3. No session state — every turn is a fresh answer (no refine path).
  4. No suppression gate — a "make it shorter" turn costs a full search.

It implements the same run_turn signature as AegisPipeline, so the API, the live
race and the offline eval all drive both systems through one code path.
"""
from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path
from typing import Optional, Sequence

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import config, synthesis  # noqa: E402
from backend.llm import LLMClient, Usage, get_client  # noqa: E402
from backend.pipeline import (  # noqa: E402
    TokenSink,
    TranscriptChunk,
    await_chunk_time,
    tokenize_stream,
)
from backend.retrieval.engine import RetrievalEngine, get_engine  # noqa: E402
from backend.schemas import SubQuery, TurnMetrics, TurnResult  # noqa: E402
from backend.telemetry import TelemetryBus  # noqa: E402


class NaivePipeline:
    system_name = "naive"

    def __init__(
        self,
        engine: Optional[RetrievalEngine] = None,
        client: Optional[LLMClient] = None,
    ) -> None:
        self.engine = engine or get_engine()
        self.client = client or get_client()

    async def run_turn(
        self,
        session_id: str,
        chunks: Sequence[TranscriptChunk],
        bus: TelemetryBus,
        on_token: Optional[TokenSink] = None,
        state=None,
        realtime: Optional[bool] = None,
    ) -> TurnResult:
        bus.reset_clock()
        turn_start = time.perf_counter()
        usage = Usage()
        live = config.REALTIME_REPLAY if realtime is None else realtime

        # 1. Wait for the whole utterance. We replay the chunk timeline so the
        #    comparison is honest: the naive system really does sit idle while
        #    Aegis is already searching.
        buffer_parts: list[str] = []
        last_t = 0.0
        for chunk in chunks:
            await await_chunk_time(chunk, turn_start, live)
            if chunk.text.strip():
                buffer_parts.append(chunk.text.strip())
            last_t = chunk.t
            await bus.emit(
                "controller_decision",
                decision="wait",
                reason="naive_baseline_waits_for_utterance_end",
                buffer=" ".join(buffer_parts),
                system=self.system_name,
            )
        utterance = " ".join(buffer_parts).strip()
        utterance_end_at = bus.elapsed_s
        await bus.emit("utterance_end", utterance=utterance, system=self.system_name)

        # 2. One query, no decomposition.
        sub_queries = [SubQuery(text=utterance)]
        await bus.emit(
            "sub_query_dispatched",
            sub_queries=[utterance],
            count=1,
            system=self.system_name,
        )
        await bus.emit(
            "retrieval_started", trigger="explicit", query=utterance,
            system=self.system_name,
        )
        results = await self.engine.search_many([utterance])
        retrieval_calls = sum(r.calls for r in results)
        retrieved_ids: list[str] = []
        for r in results:
            for cid in r.chunk_ids:
                if cid not in retrieved_ids:
                    retrieved_ids.append(cid)
        await bus.emit(
            "fusion_done", chunk_ids=retrieved_ids, system=self.system_name
        )

        # 3. Always a fresh synthesis — no session state, no delta engine.
        out = await synthesis.synthesize(
            session_id, utterance, sub_queries, results, self.engine, None, self.client
        )
        usage.add(out.usage)
        new_state = out.state
        await bus.emit(
            f"answer_v{new_state.answer_version}",
            answer_version=new_state.answer_version,
            claims=[c.model_dump() for c in new_state.claims],
            system=self.system_name,
        )

        text = new_state.answer_text() or "No supporting evidence found."
        first_token_at: Optional[float] = None
        for token in tokenize_stream(text):
            if first_token_at is None:
                first_token_at = bus.elapsed_s
                await bus.emit(
                    "first_token",
                    ttft_from_utterance_end_ms=round(
                        (first_token_at - utterance_end_at) * 1000, 2
                    ),
                    system=self.system_name,
                )
            if on_token is not None:
                await on_token(token)
        if first_token_at is None:
            first_token_at = bus.elapsed_s

        cost = usage.cost_usd() + retrieval_calls * config.USD_PER_RETRIEVAL_CALL
        metrics = TurnMetrics(
            ttft_ms=round((first_token_at - utterance_end_at) * 1000, 2),
            total_tokens=usage.total_tokens,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            estimated_cost_usd=round(cost, 8),
            retrieval_calls=retrieval_calls,
            is_refine_turn=False,
            wall_ms=round((time.perf_counter() - turn_start) * 1000, 2),
            early_start_ms=0.0,
        )
        result = TurnResult(
            retrieval_events=[
                {"timestamp_s": round(utterance_end_at, 3), "query": utterance,
                 "trigger": "explicit"}
            ],
            sub_queries=[utterance],
            answer=text,
            citations=new_state.all_citations(),
            uncertainty="; ".join(new_state.uncertainty) or None,
            answer_version=new_state.answer_version,
            retrieval_required=True,
            claims=new_state.claims,
            retrieved_chunk_ids=retrieved_ids,
            metrics=metrics,
            system=self.system_name,
        )
        await bus.emit(
            "turn_complete", result=result.model_dump(), system=self.system_name
        )
        return result


async def run(utterance: str, session_id: str = "naive") -> TurnResult:
    from backend.main import simulate_chunks  # noqa: PLC0415

    bus = TelemetryBus(session_id)
    return await NaivePipeline().run_turn(session_id, simulate_chunks(utterance), bus)


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What is the cancellation policy inside 7 days?"
    res = asyncio.run(run(q))
    print(res.answer)
    print("citations:", res.citations)
