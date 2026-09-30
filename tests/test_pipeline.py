"""Test suite.

Organised around the gates the brief actually grades: the four required
behaviours, the four metrics, and the two hard constraints (corpus isolation,
session-bound state).

Run:  pytest -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import config, controller, decomposer, suppression, synthesis  # noqa: E402
from backend.embeddings import cosine_sim, embed_one  # noqa: E402
from backend.main import simulate_chunks  # noqa: E402
from backend.pipeline import AegisPipeline, TranscriptChunk  # noqa: E402
from backend.retrieval.corpus import build_chunks  # noqa: E402
from backend.retrieval.engine import RetrievalEngine  # noqa: E402
from backend.retrieval.fusion import rrf  # noqa: E402
from backend.schemas import Decision  # noqa: E402
from backend.session_store import MemorySessionStore  # noqa: E402
from backend.telemetry import TelemetryBus  # noqa: E402



@pytest.fixture(scope="module")
def engine() -> RetrievalEngine:
    return RetrievalEngine(build_chunks())


@pytest.fixture
def pipeline(engine: RetrievalEngine) -> AegisPipeline:
    return AegisPipeline(engine=engine, store=MemorySessionStore())


async def run(pipeline: AegisPipeline, text: str, session: str = "t"):
    bus = TelemetryBus(session)
    result = await pipeline.run_turn(
        session, simulate_chunks(text), bus, realtime=False
    )
    return result, bus


# ---------------- corpus & retrieval ----------------

def test_corpus_loads_and_chunks(engine: RetrievalEngine):
    assert len(engine.chunks) > 30
    assert len({c.doc_id for c in engine.chunks}) >= 15


def test_chunk_ids_are_unique(engine: RetrievalEngine):
    ids = [c.chunk_id for c in engine.chunks]
    assert len(ids) == len(set(ids))


def test_no_content_free_chunks(engine: RetrievalEngine):
    # A bare heading scores well on keyword overlap but answers nothing.
    assert all(len(c.text.split()) >= 10 for c in engine.chunks)


def test_hybrid_search_finds_known_fact(engine: RetrievalEngine):
    result = engine.search_sync("Orchid Hall boardroom capacity 30 people")
    assert "Doc_01#c1" in result.chunk_ids


def test_rrf_rewards_consensus_across_lists():
    fused = dict(rrf([["a", "b", "c"], ["b", "a", "d"], ["b", "x", "y"]]))
    assert fused["b"] > fused["a"] > fused["c"]


def test_rrf_handles_empty_input():
    assert rrf([]) == []
    assert rrf([[], []]) == []


def test_search_with_empty_query_is_safe(engine: RetrievalEngine):
    result = engine.search_sync("   ")
    assert result.chunks == [] and result.calls == 0


# ---------------- [1] controller ----------------

def test_controller_waits_on_short_fragment():
    state = controller.ControllerState()
    d = controller.decide(state, "I need", 0.0)
    assert d.decision is Decision.WAIT


def test_controller_speculates_before_utterance_end():
    state = controller.ControllerState()
    decisions = []
    for chunk in simulate_chunks(
        "I need a venue in Pune for 30 people and the cancellation policy and catering"
    ):
        decisions.append(
            controller.decide(
                state, chunk.text, chunk.t,
                silence_s=chunk.silence_s, is_final=chunk.is_final,
            ).decision
        )
    assert Decision.PROVISIONAL_RETRIEVE in decisions, "never started early"
    # Speculation must happen strictly before the terminal decision.
    assert decisions.index(Decision.PROVISIONAL_RETRIEVE) < decisions.index(Decision.RETRIEVE)


def test_controller_always_terminates_in_retrieve():
    state = controller.ControllerState()
    last = None
    for chunk in simulate_chunks("What is the per diem rate in Pune?"):
        last = controller.decide(
            state, chunk.text, chunk.t,
            silence_s=chunk.silence_s, is_final=chunk.is_final,
        ).decision
    assert last is Decision.RETRIEVE


def test_controller_does_not_thrash(engine: RetrievalEngine):
    """Pitfall #1: retrieval must not fire on every chunk."""
    state = controller.ControllerState()
    fired = 0
    chunks = simulate_chunks(
        "I need a venue in Pune for 30 people and the cancellation policy "
        "and catering options and the reimbursement rules as well"
    )
    for chunk in chunks:
        d = controller.decide(state, chunk.text, chunk.t, is_final=chunk.is_final)
        if d.decision is Decision.PROVISIONAL_RETRIEVE:
            fired += 1
    # The property that matters is bounded re-speculation, not a single shot:
    # the controller may catch a late-arriving intent, but must never fire on
    # every chunk the way an ungated implementation would.
    assert fired < len(chunks) / 2, f"speculation thrashed ({fired}/{len(chunks)} chunks)"


def test_entity_extraction_picks_numbers_and_places():
    ents = controller.extract_entities("I need a venue in Pune for 30 people")
    assert "num:30" in ents and "ent:pune" in ents


def test_drift_falls_as_utterance_settles():
    """Consecutive-state drift must decrease, or the controller can never
    recognise a stabilising utterance."""
    state = controller.ControllerState()
    drifts = [
        controller.decide(state, c.text, c.t).drift
        for c in simulate_chunks("What is the cancellation fee inside 7 days of the event")
    ]
    assert drifts[-1] < drifts[1]


def test_always_wait_mode_disables_speculation():
    original = config.CONTROLLER_MODE
    config.CONTROLLER_MODE = "always_wait"
    try:
        state = controller.ControllerState()
        decisions = [
            controller.decide(state, c.text, c.t, is_final=c.is_final).decision
            for c in simulate_chunks("I need a venue in Pune for 30 people and catering")
        ]
        assert Decision.PROVISIONAL_RETRIEVE not in decisions
    finally:
        config.CONTROLLER_MODE = original


# ---------------- [2] decomposer ----------------

def test_compound_utterance_splits_into_multiple_queries():
    subs = decomposer.heuristic_decompose(
        "I need a Pune venue for 30 people and the cancellation policy and catering options"
    )
    assert len(subs) >= 2


def test_llm_subquery_context_is_normalized_without_duplication():
    utterance = (
        "find a venue to accommodate 30 people in Pune and "
        "retrieve the cancellation policy for the venue in Pune"
    )
    raw = [
        "find a venue to accommodate 30 people in Pune",
        "retrieve the cancellation policy for the venue in Pune",
    ]
    assert decomposer.contextualize_subqueries(utterance, raw) == [
        "find a venue to accommodate 30 people in Pune",
        "retrieve the cancellation policy for the venue in Pune",
    ]


def test_llm_short_cancellation_query_gets_explicit_context():
    utterance = (
        "find a venue to accommodate 30 people in Pune and "
        "retrieve the cancellation"
    )
    raw = [
        "find a venue to accommodate 30 people in Pune",
        "retrieve the cancellation",
    ]
    assert decomposer.contextualize_subqueries(utterance, raw) == [
        "find a venue to accommodate 30 people in Pune",
        "retrieve the cancellation policy for the venue in Pune",
    ]


@pytest.mark.asyncio
async def test_llm_path_dispatches_normalized_queries():
    class FakeLLM:
        is_stub = False

        async def complete_json(self, *args, **kwargs):
            from backend.llm import Usage
            return (
                {
                    "sub_queries": [
                        "find a venue to accommodate 30 people in Pune",
                        "retrieve the cancellation policy for the venue policy for venue in Pune venue Pune Pune",
                    ]
                },
                Usage(calls=1),
            )

    subs, _ = await decomposer.decompose(
        "find a venue to accommodate 30 people in Pune and "
        "retrieve the cancellation policy for the venue in Pune",
        FakeLLM(),
    )
    assert [s.text for s in subs] == [
        "find a venue to accommodate 30 people in Pune",
        "retrieve the cancellation policy for the venue in Pune",
    ]


def test_simple_question_is_not_over_fragmented():
    subs = decomposer.heuristic_decompose("What is the per diem rate in Pune?")
    assert len(subs) == 1


def test_orthogonality_guard_drops_duplicates():
    dupes = ["cancellation policy", "cancellation policy", "catering options"]
    assert len(decomposer.dedup_subqueries(dupes)) == 2


def test_decomposer_never_exceeds_cap():
    long = " and ".join([f"question number {i} about venues" for i in range(10)])
    assert len(decomposer.heuristic_decompose(long)) <= config.MAX_SUB_QUERIES


async def test_decompose_always_returns_something():
    subs, _ = await decomposer.decompose("hmm")
    assert subs and subs[0].text


def test_refine_detection_on_correction_marker():
    is_refine, _ = decomposer.is_refine_turn(
        "Actually make that 60 people", "venue for 30 people", ["Orchid Hall seats 30."]
    )
    assert is_refine


def test_new_topic_is_not_treated_as_refine():
    is_refine, _ = decomposer.is_refine_turn(
        "How long are event recordings retained?",
        "venue for 30 people in Pune",
        ["Orchid Hall seats 30 people in boardroom layout."],
    )
    assert not is_refine


def test_refine_requires_prior_state():
    is_refine, _ = decomposer.is_refine_turn("Actually make it 60", "", [])
    assert not is_refine


# ---------------- [4.5] suppression ----------------

@pytest.mark.parametrize(
    "text", ["Make that shorter", "Turn it into bullet points", "Translate that to Hindi"]
)
def test_presentation_turns_are_suppressed(text: str):
    assert suppression.classify(text, has_session_state=True).is_presentation_only


def test_suppression_requires_existing_answer():
    assert not suppression.classify("Make that shorter", has_session_state=False).is_presentation_only


def test_transform_verb_plus_new_question_is_not_suppressed():
    r = suppression.classify(
        "Make it shorter and what is the catering cost per head?", has_session_state=True
    )
    assert not r.is_presentation_only


# ---------------- [4] synthesis & grounding ----------------

def test_verify_claim_rejects_unsupported_text(engine: RetrievalEngine):
    evidence = engine.search_sync("cancellation policy notice tiers").chunks
    _, _, _, uncertain = synthesis.verify_claim(
        "Employees receive 26 weeks of fully paid parental leave.", evidence, engine
    )
    assert uncertain


def test_verify_claim_accepts_supported_text(engine: RetrievalEngine):
    evidence = engine.search_sync("Orchid Hall capacity").chunks
    ids, cites, _, uncertain = synthesis.verify_claim(
        evidence[0].chunk.text, evidence, engine
    )
    assert not uncertain and ids and cites


def test_verify_claim_ignores_ids_outside_the_index(engine: RetrievalEngine):
    """Corpus isolation: an ID not in the live index can never be cited."""
    from backend.schemas import Chunk, ScoredChunk

    fake = ScoredChunk(
        chunk=Chunk(chunk_id="Doc_99#c9", doc_id="Doc_99", section="§1",
                    text="Invented policy text about venues.", citation="Doc_99 §1"),
        score=1.0,
    )
    ids, _, _, uncertain = synthesis.verify_claim("Invented policy text about venues.", [fake], engine)
    assert ids == [] and uncertain


# ---------------- end-to-end behaviours ----------------

async def test_turn_produces_grounded_cited_answer(pipeline, engine):
    result, _ = await run(pipeline, "What is the cancellation fee inside 7 days?")
    assert result.claims
    for claim in result.claims:
        assert claim.chunk_ids
        assert all(engine.exists(cid) for cid in claim.chunk_ids)


async def test_no_fabricated_document_ids(pipeline, engine):
    for q in [
        "What is the catering cost per head?",
        "Who approves a cancellation inside 48 hours?",
        "What is the parental leave policy?",
    ]:
        result, _ = await run(pipeline, q, session=f"fab_{hash(q)}")
        for claim in result.claims:
            assert all(engine.exists(cid) for cid in claim.chunk_ids)


async def test_out_of_corpus_question_flags_uncertainty(pipeline):
    result, _ = await run(pipeline, "What is the parental leave policy and how many weeks are paid?")
    assert result.uncertainty, "must decline rather than answer from parametric knowledge"


async def test_multi_intent_dispatches_multiple_sub_queries(pipeline):
    result, bus = await run(
        pipeline,
        "I need a Pune venue for 30 people and the cancellation policy and catering options",
    )
    assert len(result.sub_queries) >= 2
    assert bus.events_of("sub_query_dispatched")


async def test_refine_turn_patches_instead_of_restarting(pipeline):
    first, _ = await run(pipeline, "I need a venue in Pune for 30 people and the cancellation policy", "s")
    second, _ = await run(pipeline, "Actually make that 60 people", "s")

    assert second.metrics.is_refine_turn
    assert second.answer_version > first.answer_version
    # "Refine, don't restart": some claim must survive untouched from v1.
    assert any(c.status == "unchanged" for c in second.claims)
    # And it must be cheaper than the fresh turn that preceded it.
    assert second.metrics.retrieval_calls <= first.metrics.retrieval_calls


async def test_presentation_turn_costs_zero_retrieval(pipeline):
    await run(pipeline, "What is the expense submission deadline and the approval chain?", "p")
    second, _ = await run(pipeline, "Make that shorter", "p")
    assert second.retrieval_required is False
    assert second.metrics.retrieval_calls == 0
    assert second.suppression_reason


async def test_answer_version_increments_monotonically(pipeline):
    versions = []
    for text in [
        "What is the catering cost per head?",
        "Also what about dietary accommodation?",
        "Make that shorter",
    ]:
        result, _ = await run(pipeline, text, "v")
        versions.append(result.answer_version)
    assert versions == sorted(versions) and len(set(versions)) == len(versions)


# ---------------- telemetry ----------------

async def test_every_stage_emits_telemetry(pipeline):
    _, bus = await run(pipeline, "What is the cancellation policy and the catering cost?")
    names = {e["event"] for e in bus.events}
    for required in {
        "controller_decision", "sub_query_dispatched", "retrieval_started",
        "fusion_done", "first_token", "turn_complete",
    }:
        assert required in names, f"missing telemetry event: {required}"


async def test_telemetry_events_carry_required_fields(pipeline):
    _, bus = await run(pipeline, "What is the per diem rate?")
    for e in bus.events:
        assert "timestamp_s" in e and "session_id" in e and "event" in e


async def test_run_log_is_written(pipeline, tmp_path):
    _, bus = await run(pipeline, "What is the per diem rate in Pune?")
    bus._log_dir = tmp_path
    path = bus.flush()
    assert path.exists() and path.read_text().strip()


# ---------------- session-bound state ----------------

async def test_sessions_do_not_leak_into_each_other(pipeline):
    await run(pipeline, "What is the catering cost per head?", "session_a")
    state_b = await pipeline.store.get("session_b")
    assert state_b is None


async def test_session_state_is_keyed_only_by_session_id():
    store = MemorySessionStore()
    from backend.schemas import AnswerState

    await store.set(AnswerState(session_id="abc"))
    assert list(store._data.keys()) == ["session:abc:answer_state"]
    await store.delete("abc")
    assert await store.get("abc") is None


# ---------------- metrics ----------------

async def test_metrics_are_populated(pipeline):
    result, _ = await run(pipeline, "What is the cancellation policy?")
    m = result.metrics
    assert m.retrieval_calls > 0
    assert m.wall_ms > 0
    assert m.estimated_cost_usd >= 0


async def test_speculation_completes_work_before_utterance_end(engine):
    """The full-duplex claim, as a test rather than a slide.

    Asserts the *mechanism* — that retrieval work is finished early and reused —
    rather than racing two wall-clock numbers. A raw TTFT comparison is timing
    dependent (whether the last speculation lands before the final chunk varies
    with machine load), so it belongs in the benchmark report, where it is
    measured over 26 queries. Here we check the thing that causes the win.
    """
    original = (config.RETRIEVAL_LATENCY_MS, config.SIM_SPEED)
    config.RETRIEVAL_LATENCY_MS, config.SIM_SPEED = 80.0, 1.0
    try:
        text = ("I need a venue in Pune for 30 people and I want to know "
                "the cancellation policy and the catering options")
        aegis = AegisPipeline(engine=engine, store=MemorySessionStore())
        bus = TelemetryBus("spec")
        result = await aegis.run_turn("spec", simulate_chunks(text), bus, realtime=True)

        # Retrieval genuinely began before the user stopped speaking.
        assert result.metrics.early_start_ms > 0
        assert any(
            e["event"] == "retrieval_started" and e.get("trigger") == "provisional"
            for e in bus.events
        )
        # And that early work was actually consumed, not recomputed.
        fusion = bus.events_of("fusion_done")
        assert fusion and fusion[-1]["reused_provisional"] >= 1
    finally:
        config.RETRIEVAL_LATENCY_MS, config.SIM_SPEED = original


async def test_naive_baseline_never_speculates(engine):
    """Control arm sanity: if the baseline also started early, every latency
    comparison in the report would be meaningless."""
    from eval.baseline_naive_rag import NaivePipeline

    bus = TelemetryBus("naive")
    await NaivePipeline(engine=engine).run_turn(
        "naive", simulate_chunks("I need a Pune venue for 30 people and catering"),
        bus, realtime=False,
    )
    assert not any(e.get("trigger") == "provisional" for e in bus.events)
    decisions = {e.get("decision") for e in bus.events_of("controller_decision")}
    assert decisions == {"wait"}


# ---------------- embeddings ----------------

def test_embeddings_are_deterministic():
    assert cosine_sim(embed_one("cancellation policy"), embed_one("cancellation policy")) == pytest.approx(1.0, abs=1e-5)


def test_related_text_scores_above_unrelated():
    base = embed_one("venue booking cancellation fee")
    near = embed_one("cancellation charge for the venue")
    far = embed_one("recordings are retained for ninety days")
    assert cosine_sim(base, near) > cosine_sim(base, far)


def test_empty_text_embeds_without_crashing():
    assert embed_one("").shape[0] > 0

# ---------------- live WebSocket-style ingestion ----------------

async def test_live_turn_processes_chunks_before_end(engine: RetrievalEngine):
    p = AegisPipeline(engine=engine, store=MemorySessionStore())
    bus = TelemetryBus("live")
    live = await p.begin_live_turn("live", bus)
    await p.ingest_live_chunk(live, TranscriptChunk(t=0.0, text="I need a venue in Pune"))
    await p.ingest_live_chunk(live, TranscriptChunk(t=0.3, text=" for 30 people"))
    await p.ingest_live_chunk(live, TranscriptChunk(t=0.6, text=" and catering options"))
    # No final answer yet, but controller telemetry/speculation already exists.
    decisions = [e.get("decision") for e in bus.events if e.get("event") == "controller_decision"]
    assert decisions
    assert Decision.PROVISIONAL_RETRIEVE in decisions
    result = await p.finish_live_turn(live)
    assert result.answer


async def test_unrelated_topic_does_not_reuse_old_claims(engine: RetrievalEngine):
    p = AegisPipeline(engine=engine, store=MemorySessionStore())
    bus = TelemetryBus("topic")
    first = await p.run_turn("topic", simulate_chunks("I need a venue in Pune for 30 people"), bus, realtime=False)
    assert first.claims
    bus2 = TelemetryBus("topic")
    second = await p.run_turn("topic", simulate_chunks("What is the parental leave policy?"), bus2, realtime=False)
    assert not second.metrics.is_refine_turn
    assert second.claims == []
    assert second.uncertainty
