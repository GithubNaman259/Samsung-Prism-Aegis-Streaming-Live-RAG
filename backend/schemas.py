"""Pydantic contracts. These are the wire format for the WebSocket, the JSONL
run log, and eval/run_eval.py. Mirrors architecture.md §5 and PRD §7."""
from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class Decision(str, Enum):
    WAIT = "wait"
    PROVISIONAL_RETRIEVE = "provisional_retrieve"
    RETRIEVE = "retrieve"
    SUPPRESS = "suppress"


class Chunk(BaseModel):
    """One retrievable unit of the corpus."""
    chunk_id: str
    doc_id: str
    section: str
    text: str
    citation: str  # human-facing label, e.g. "Doc_12 §2"


class ScoredChunk(BaseModel):
    chunk: Chunk
    score: float
    source: str = "fused"  # sparse | dense | fused | reranked


class SubQuery(BaseModel):
    text: str
    intent: str = "general"


class Claim(BaseModel):
    claim_id: str
    text: str
    citations: list[str] = Field(default_factory=list)
    chunk_ids: list[str] = Field(default_factory=list)
    status: str = "unchanged"  # unchanged | added_in_v{n} | modified_in_v{n}
    confidence: float = 0.0
    is_uncertain: bool = False


class AnswerState(BaseModel):
    """Versioned answer state, session-scoped only (architecture.md §4)."""
    session_id: str
    answer_version: int = 0
    created_at: float = 0.0
    claims: list[Claim] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)
    turn_history: list[dict[str, Any]] = Field(default_factory=list)
    last_utterance: str = ""
    known_chunk_ids: list[str] = Field(default_factory=list)

    def answer_text(self) -> str:
        return " ".join(c.text for c in self.claims).strip()

    def all_citations(self) -> list[str]:
        seen: list[str] = []
        for c in self.claims:
            for cit in c.citations:
                if cit not in seen:
                    seen.append(cit)
        return seen


# ---------------- Telemetry events ----------------

class ControllerDecisionEvent(BaseModel):
    event: Literal["controller_decision"] = "controller_decision"
    timestamp_s: float
    decision: Literal["wait", "provisional_retrieve", "retrieve", "suppress"]
    reason: str


class SubQueryDispatchEvent(BaseModel):
    event: Literal["sub_query_dispatched"] = "sub_query_dispatched"
    timestamp_s: float
    sub_queries: list[str]


class TurnMetrics(BaseModel):
    ttft_ms: float = 0.0
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    retrieval_calls: int = 0
    is_refine_turn: bool = False
    wall_ms: float = 0.0
    early_start_ms: float = 0.0  # how long before utterance-end retrieval began


class TurnResult(BaseModel):
    """Final structured output — PRD §7 response contract, extended with the
    fields the eval harness needs."""
    retrieval_events: list[dict[str, Any]] = Field(default_factory=list)
    sub_queries: list[str] = Field(default_factory=list)
    answer: str = ""
    citations: list[str] = Field(default_factory=list)
    uncertainty: Optional[str] = None
    answer_version: int = 0
    retrieval_required: bool = True
    suppression_reason: Optional[str] = None
    claims: list[Claim] = Field(default_factory=list)
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    metrics: TurnMetrics = Field(default_factory=TurnMetrics)
    system: str = "aegis"
