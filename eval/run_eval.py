"""Automated eval harness — the four required metrics.

  1. Retrieval recall      (architecture.md §6.1) measured after fusion+rerank
  2. Answer groundedness   (§6.2) + fabricated-ID rate, which must be exactly 0
  3. Time-to-first-token   (§6.3) Aegis vs naive baseline
  4. Cost per turn         (§6.4) fresh turns vs refine turns

Also runs the ablations from §7 and the Trust Gauntlet, then writes
eval/report.md. The live demo calls these same functions — there is no
separate demo-only measurement path.

Usage:
    python -m eval.run_eval                 # full run, writes eval/report.md
    python -m eval.run_eval --quick         # metrics only, skip ablations
    python -m eval.run_eval --json out.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Sequence

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import config, synthesis  # noqa: E402
from backend.pipeline import AegisPipeline  # noqa: E402
from backend.retrieval.engine import RetrievalEngine, set_engine  # noqa: E402
from backend.schemas import TurnResult  # noqa: E402
from backend.session_store import MemorySessionStore  # noqa: E402
from backend.telemetry import TelemetryBus  # noqa: E402
from eval.baseline_naive_rag import NaivePipeline  # noqa: E402

EVAL_DIR = ROOT / "eval"
TESTSET = EVAL_DIR / "testset.jsonl"
GAUNTLET = EVAL_DIR / "gauntlet.jsonl"
REPORT = EVAL_DIR / "report.md"

# Multi-turn conversations exercising the refine path and the suppression gate.
REFINE_SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "s1",
        "turns": [
            "I need a venue in Pune for 30 people and I want to know the cancellation policy.",
            "Actually make that 60 people.",
        ],
    },
    {
        "id": "s2",
        "turns": [
            "What are the catering options and the per head cost?",
            "Also we need vegan and gluten free.",
        ],
    },
    {
        "id": "s3",
        "turns": [
            "Tell me the expense submission deadline and the approval chain.",
            "Make that shorter.",
        ],
    },
]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _chunks(utterance: str):
    from backend.main import simulate_chunks  # noqa: PLC0415

    return simulate_chunks(utterance)


def mean(values: Sequence[float]) -> float:
    return round(statistics.fmean(values), 4) if values else 0.0


# ---------------- metric 1: retrieval recall ----------------

@dataclass
class RecallRow:
    id: str
    type: str
    query: str
    recall: float
    hit: int
    gold: int
    retrieved: list[str] = field(default_factory=list)
    sub_queries: list[str] = field(default_factory=list)


async def measure_recall(pipeline, rows: Sequence[dict[str, Any]], label: str) -> dict[str, Any]:
    out: list[RecallRow] = []
    for row in rows:
        bus = TelemetryBus(f"recall_{label}_{row['id']}")
        result = await pipeline.run_turn(
            f"recall_{label}_{row['id']}", _chunks(row["query"]), bus, state=None,
            realtime=False,
        )
        gold = set(row["gold_chunk_ids"])
        got = set(result.retrieved_chunk_ids)
        hit = len(gold & got)
        out.append(
            RecallRow(
                id=row["id"], type=row.get("type", "single"), query=row["query"],
                recall=round(hit / max(len(gold), 1), 4), hit=hit, gold=len(gold),
                retrieved=result.retrieved_chunk_ids,
                sub_queries=result.sub_queries,
            )
        )
    singles = [r.recall for r in out if r.type == "single"]
    multis = [r.recall for r in out if r.type == "multi"]
    return {
        "label": label,
        "overall": mean([r.recall for r in out]),
        "single_intent": mean(singles),
        "multi_intent": mean(multis),
        "n": len(out),
        "rows": [r.__dict__ for r in out],
    }


# ---------------- metric 2: groundedness ----------------

async def measure_groundedness(
    pipeline, rows: Sequence[dict[str, Any]], engine: RetrievalEngine, label: str
) -> dict[str, Any]:
    total_claims = 0
    supported = 0
    fabricated = 0
    uncertain_turns = 0
    details: list[dict[str, Any]] = []

    for row in rows:
        bus = TelemetryBus(f"ground_{label}_{row['id']}")
        result = await pipeline.run_turn(
            f"ground_{label}_{row['id']}", _chunks(row["query"]), bus, state=None,
            realtime=False,
        )
        if result.uncertainty:
            uncertain_turns += 1
        for claim in result.claims:
            total_claims += 1
            real_ids = [cid for cid in claim.chunk_ids if engine.exists(cid)]
            fabricated += len(claim.chunk_ids) - len(real_ids)
            ok = any(
                synthesis.entails(engine.by_id[cid].text, claim.text) for cid in real_ids
            )
            if ok:
                supported += 1
            else:
                details.append(
                    {"query_id": row["id"], "claim": claim.text[:160],
                     "chunk_ids": claim.chunk_ids}
                )
    return {
        "label": label,
        "groundedness": round(supported / total_claims, 4) if total_claims else 0.0,
        "claims_sampled": total_claims,
        "claims_supported": supported,
        "fabricated_id_rate": round(fabricated / total_claims, 6) if total_claims else 0.0,
        "fabricated_ids": fabricated,
        "turns_with_uncertainty": uncertain_turns,
        "unsupported_examples": details[:10],
    }


# ---------------- metric 3: TTFT ----------------

async def measure_ttft(
    aegis: AegisPipeline, naive: NaivePipeline, rows: Sequence[dict[str, Any]]
) -> dict[str, Any]:
    """Latency is the one metric that must be measured on a true real-time
    clock. Compressing the replay clock (SIM_SPEED < 1) shrinks the speech
    timeline while leaving retrieval latency at wall-clock scale, which
    destroys the speech-to-retrieval ratio the whole full-duplex claim depends
    on. So this function forces SIM_SPEED = 1.0 regardless of the CLI flag.
    That makes it the slowest part of the run, and correctly so."""
    saved_speed = config.SIM_SPEED
    config.SIM_SPEED = 1.0
    aegis_ttft: list[float] = []
    naive_ttft: list[float] = []
    by_type: dict[str, dict[str, list[float]]] = {}
    aegis_wall: list[float] = []
    naive_wall: list[float] = []
    early: list[float] = []

    for row in rows:
        a_bus = TelemetryBus(f"ttft_a_{row['id']}")
        n_bus = TelemetryBus(f"ttft_n_{row['id']}")
        a = await aegis.run_turn(
            f"ttft_a_{row['id']}", _chunks(row["query"]), a_bus, state=None, realtime=True
        )
        n = await naive.run_turn(
            f"ttft_n_{row['id']}", _chunks(row["query"]), n_bus, realtime=True
        )
        aegis_ttft.append(a.metrics.ttft_ms)
        naive_ttft.append(n.metrics.ttft_ms)
        bucket = by_type.setdefault(
            row.get("type", "single"), {"aegis": [], "naive": []}
        )
        bucket["aegis"].append(a.metrics.ttft_ms)
        bucket["naive"].append(n.metrics.ttft_ms)
        aegis_wall.append(a.metrics.wall_ms)
        naive_wall.append(n.metrics.wall_ms)
        early.append(a.metrics.early_start_ms)

    config.SIM_SPEED = saved_speed
    med_a = round(statistics.median(aegis_ttft), 2) if aegis_ttft else 0.0
    med_n = round(statistics.median(naive_ttft), 2) if naive_ttft else 0.0
    return {
        "aegis_median_ttft_ms": med_a,
        "naive_median_ttft_ms": med_n,
        "ttft_reduction_ms": round(med_n - med_a, 2),
        "ttft_reduction_pct": round((med_n - med_a) / med_n * 100, 2) if med_n else 0.0,
        "aegis_median_wall_ms": round(statistics.median(aegis_wall), 2) if aegis_wall else 0.0,
        "naive_median_wall_ms": round(statistics.median(naive_wall), 2) if naive_wall else 0.0,
        "median_early_start_ms": round(statistics.median(early), 2) if early else 0.0,
        "by_type": {
            k: {
                "aegis_median_ttft_ms": round(statistics.median(v["aegis"]), 2),
                "naive_median_ttft_ms": round(statistics.median(v["naive"]), 2),
                "reduction_ms": round(
                    statistics.median(v["naive"]) - statistics.median(v["aegis"]), 2
                ),
                "n": len(v["aegis"]),
            }
            for k, v in by_type.items()
        },
        "n": len(rows),
    }


# ---------------- metric 4: cost per turn ----------------

async def measure_cost(aegis: AegisPipeline, naive: NaivePipeline) -> dict[str, Any]:
    fresh: list[TurnResult] = []
    refine: list[TurnResult] = []
    suppressed: list[TurnResult] = []
    naive_equiv: list[TurnResult] = []
    transcript: list[dict[str, Any]] = []

    for scenario in REFINE_SCENARIOS:
        session = f"cost_{scenario['id']}"
        aegis.store = MemorySessionStore()  # isolate each scenario
        for i, utterance in enumerate(scenario["turns"]):
            bus = TelemetryBus(f"{session}_t{i}")
            result = await aegis.run_turn(
                session, _chunks(utterance), bus, realtime=False
            )
            if not result.retrieval_required:
                suppressed.append(result)
            elif result.metrics.is_refine_turn:
                refine.append(result)
            else:
                fresh.append(result)
            transcript.append(
                {
                    "scenario": scenario["id"], "turn": i + 1, "utterance": utterance,
                    "retrieval_required": result.retrieval_required,
                    "is_refine_turn": result.metrics.is_refine_turn,
                    "retrieval_calls": result.metrics.retrieval_calls,
                    "sub_queries": len(result.sub_queries),
                    "tokens": result.metrics.total_tokens,
                    "cost_usd": result.metrics.estimated_cost_usd,
                    "answer_version": result.answer_version,
                }
            )
            # The naive baseline has no session state, so every follow-up costs
            # a full fresh turn. That is the comparison the metric exists for.
            n_bus = TelemetryBus(f"{session}_naive_t{i}")
            naive_equiv.append(
                await naive.run_turn(
                    f"{session}_naive", _chunks(utterance), n_bus, realtime=False
                )
            )

    def agg(rows: Sequence[TurnResult]) -> dict[str, Any]:
        return {
            "n": len(rows),
            "mean_retrieval_calls": mean([r.metrics.retrieval_calls for r in rows]),
            "mean_sub_queries": mean([len(r.sub_queries) for r in rows]),
            "mean_tokens": mean([r.metrics.total_tokens for r in rows]),
            "mean_cost_usd": round(
                statistics.fmean([r.metrics.estimated_cost_usd for r in rows]), 8
            ) if rows else 0.0,
        }

    fresh_agg, refine_agg = agg(fresh), agg(refine)
    reduction = 0.0
    if fresh_agg["mean_retrieval_calls"]:
        reduction = round(
            (1 - refine_agg["mean_retrieval_calls"] / fresh_agg["mean_retrieval_calls"]) * 100, 2
        )
    return {
        "fresh_turns": fresh_agg,
        "refine_turns": refine_agg,
        "suppressed_turns": agg(suppressed),
        "naive_all_turns": agg(naive_equiv),
        "refine_retrieval_call_reduction_pct": reduction,
        "transcript": transcript,
    }


# ---------------- ablations ----------------

async def run_ablations(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Each arm flips one config flag and re-measures recall + latency."""
    arms = [
        ("hybrid (BM25 + dense)", {"USE_SPARSE": True, "USE_DENSE": True, "USE_RERANKER": True}),
        ("dense only", {"USE_SPARSE": False, "USE_DENSE": True, "USE_RERANKER": True}),
        ("sparse only", {"USE_SPARSE": True, "USE_DENSE": False, "USE_RERANKER": True}),
        ("hybrid, no reranker", {"USE_SPARSE": True, "USE_DENSE": True, "USE_RERANKER": False}),
    ]
    original = {k: getattr(config, k) for _, flags in arms for k in flags}
    out: list[dict[str, Any]] = []
    try:
        for name, flags in arms:
            for key, value in flags.items():
                setattr(config, key, value)
            pipeline = AegisPipeline(store=MemorySessionStore())
            started = time.perf_counter()
            recall = await measure_recall(pipeline, rows, name)
            elapsed_ms = (time.perf_counter() - started) * 1000 / max(len(rows), 1)
            out.append(
                {
                    "arm": name,
                    "recall_overall": recall["overall"],
                    "recall_single": recall["single_intent"],
                    "recall_multi": recall["multi_intent"],
                    "mean_latency_ms_per_query": round(elapsed_ms, 2),
                }
            )
    finally:
        for key, value in original.items():
            setattr(config, key, value)
    return out


async def run_controller_ablation(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rule-based speculative controller vs. a wait-for-end controller."""
    original = config.CONTROLLER_MODE
    saved_speed = config.SIM_SPEED
    config.SIM_SPEED = 1.0
    out: list[dict[str, Any]] = []
    try:
        for mode in ("rule", "always_wait"):
            config.CONTROLLER_MODE = mode
            pipeline = AegisPipeline(store=MemorySessionStore())
            ttfts: list[float] = []
            earlies: list[float] = []
            for row in rows:
                bus = TelemetryBus(f"ctrl_{mode}_{row['id']}")
                res = await pipeline.run_turn(
                    f"ctrl_{mode}_{row['id']}", _chunks(row["query"]), bus, state=None,
                    realtime=True,
                )
                ttfts.append(res.metrics.ttft_ms)
                earlies.append(res.metrics.early_start_ms)
            out.append(
                {
                    "arm": f"controller={mode}",
                    "median_ttft_ms": round(statistics.median(ttfts), 2) if ttfts else 0.0,
                    "median_early_start_ms": round(statistics.median(earlies), 2) if earlies else 0.0,
                }
            )
    finally:
        config.CONTROLLER_MODE = original
        config.SIM_SPEED = saved_speed
    return out


# ---------------- gauntlet ----------------

async def run_gauntlet(pipeline: AegisPipeline, engine: RetrievalEngine) -> list[dict[str, Any]]:
    rows = load_jsonl(GAUNTLET)
    out: list[dict[str, Any]] = []
    for row in rows:
        bus = TelemetryBus(f"gauntlet_{row['id']}")
        result = await pipeline.run_turn(
            f"gauntlet_{row['id']}", _chunks(row["query"]), bus, state=None,
            realtime=False,
        )
        fabricated = sum(
            1 for c in result.claims for cid in c.chunk_ids if not engine.exists(cid)
        )
        flagged = bool(result.uncertainty)
        passed = (not row.get("must_flag_uncertainty") or flagged) and fabricated == 0
        out.append(
            {
                "id": row["id"], "kind": row["kind"], "query": row["query"],
                "flagged_uncertainty": flagged,
                "uncertainty": result.uncertainty,
                "fabricated_ids": fabricated,
                "claims": len(result.claims),
                "passed": passed,
            }
        )
    return out


# ---------------- report ----------------

def render_report(data: dict[str, Any]) -> str:
    r = data["recall"]
    g = data["groundedness"]
    t = data["ttft"]
    c = data["cost"]
    gn = data.get("groundedness_naive", {})
    rn = data.get("recall_naive", {})

    lines: list[str] = [
        "# Aegis — Benchmark Report",
        "",
        f"_Generated: {data['generated_at']}_  ",
        f"_Encoder: `{data['env']['embedding_backend']}` · LLM provider: "
        f"`{data['env']['llm_provider']}` · {data['env']['chunks']} chunks / "
        f"{data['env']['documents']} docs_",
        "",
        "Every number below comes from `eval/run_eval.py`. The live demo",
        "scoreboard calls the same functions — there is no demo-only path.",
        "",
        "## 1. The four required metrics",
        "",
        "| Metric | Aegis | Naive baseline | Target | Status |",
        "|---|---|---|---|---|",
    ]

    def status(ok: bool) -> str:
        return "PASS" if ok else "REVIEW"

    lines += [
        f"| Retrieval recall (overall) | {r['overall']:.1%} | "
        f"{rn.get('overall', 0):.1%} | ≥80% | {status(r['overall'] >= 0.80)} |",
        f"| Answer groundedness | {g['groundedness']:.1%} | "
        f"{gn.get('groundedness', 0):.1%} | ≥85% | {status(g['groundedness'] >= 0.85)} |",
        f"| Fabricated document IDs | {g['fabricated_ids']} | "
        f"{gn.get('fabricated_ids', 0)} | exactly 0 | {status(g['fabricated_ids'] == 0)} |",
        f"| Median TTFT (from utterance end) | {t['aegis_median_ttft_ms']} ms | "
        f"{t['naive_median_ttft_ms']} ms | below baseline | "
        f"{status(t['aegis_median_ttft_ms'] <= t['naive_median_ttft_ms'])} |",
        f"| Mean retrieval calls, refine turn | {c['refine_turns']['mean_retrieval_calls']} | "
        f"{c['naive_all_turns']['mean_retrieval_calls']} (no refine path) | "
        f"below fresh turn | {status(c['refine_retrieval_call_reduction_pct'] > 0)} |",
        "",
        "### 1.1 Recall split by query type",
        "",
        "| Query type | Aegis recall | Naive recall | n |",
        "|---|---|---|---|",
        f"| Single-intent | {r['single_intent']:.1%} | {rn.get('single_intent', 0):.1%} | "
        f"{sum(1 for x in r['rows'] if x['type'] == 'single')} |",
        f"| Multi-intent | {r['multi_intent']:.1%} | {rn.get('multi_intent', 0):.1%} | "
        f"{sum(1 for x in r['rows'] if x['type'] == 'multi')} |",
        "",
        "Decomposition is what the multi-intent row measures: the naive system",
        "issues one query for a question that implies several, so it can only",
        "reach the gold chunks that happen to rank under a single embedding.",
        "",
        "### 1.2 Time-to-first-token",
        "",
        f"- Aegis median TTFT: **{t['aegis_median_ttft_ms']} ms**",
        f"- Naive median TTFT: **{t['naive_median_ttft_ms']} ms**",
        f"- Reduction: **{t['ttft_reduction_ms']} ms ({t['ttft_reduction_pct']}%)**",
        f"- Median head start from speculative retrieval: "
        f"**{t['median_early_start_ms']} ms** of work completed before utterance end",
        "",
        "TTFT is measured server-side from utterance end to the first streamed",
        "token, exactly as specified in architecture.md §6.3.",
        "",
        "#### TTFT split by query type",
        "",
        "| Query type | Aegis | Naive | Reduction | n |",
        "|---|---|---|---|---|",
    ] + [
        f"| {k.title()}-intent | {v['aegis_median_ttft_ms']} ms | "
        f"{v['naive_median_ttft_ms']} ms | {v['reduction_ms']} ms | {v['n']} |"
        for k, v in sorted(t.get("by_type", {}).items())
    ] + [
        "",
        "This split is the honest version of the full-duplex claim. Speculative",
        "retrieval can only help when there is enough utterance left to overlap",
        "with: a short single-intent question ends before the controller has",
        "anything worth speculating on, so Aegis correctly matches the baseline",
        "there rather than beating it. The win lands on long compound utterances",
        "— which is exactly the case the brief describes.",
        "",
        "### 1.3 Cost per turn",
        "",
        "| Turn type | n | Mean retrieval calls | Mean sub-queries | Mean tokens | Mean cost USD |",
        "|---|---|---|---|---|---|",
    ]
    for label, key in (
        ("Fresh (Aegis)", "fresh_turns"),
        ("Refine (Aegis)", "refine_turns"),
        ("Suppressed (Aegis)", "suppressed_turns"),
        ("All turns (naive)", "naive_all_turns"),
    ):
        a = c[key]
        lines.append(
            f"| {label} | {a['n']} | {a['mean_retrieval_calls']} | "
            f"{a['mean_sub_queries']} | {a['mean_tokens']} | {a['mean_cost_usd']:.8f} |"
        )
    lines += [
        "",
        f"Refine turns issue **{c['refine_retrieval_call_reduction_pct']}% fewer "
        "retrieval calls** than fresh turns. Presentation-only turns issue zero.",
        "That is 'sharpen, don't restart' as a number rather than a claim.",
        "",
        "#### Turn-by-turn transcript",
        "",
        "| Scenario | Turn | Utterance | Retrieval? | Refine? | Calls | Version |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in c["transcript"]:
        utt = row["utterance"][:58] + ("…" if len(row["utterance"]) > 58 else "")
        lines.append(
            f"| {row['scenario']} | {row['turn']} | {utt} | "
            f"{'yes' if row['retrieval_required'] else 'NO'} | "
            f"{'yes' if row['is_refine_turn'] else 'no'} | "
            f"{row['retrieval_calls']} | v{row['answer_version']} |"
        )

    if data.get("ablations"):
        lines += [
            "",
            "## 2. Ablations",
            "",
            "### 2.1 Retrieval composition",
            "",
            "| Arm | Recall overall | Single | Multi | Mean latency/query |",
            "|---|---|---|---|---|",
        ]
        for arm in data["ablations"]:
            lines.append(
                f"| {arm['arm']} | {arm['recall_overall']:.1%} | "
                f"{arm['recall_single']:.1%} | {arm['recall_multi']:.1%} | "
                f"{arm['mean_latency_ms_per_query']} ms |"
            )
        lines += [
            "",
            "Read this table honestly: if the reranker arm is within noise of the",
            "full hybrid arm, the reranker has not earned its latency on this",
            "corpus, and the parsimony rule says report that rather than hide it.",
        ]

    if data.get("controller_ablation"):
        lines += [
            "",
            "### 2.2 Controller policy",
            "",
            "| Arm | Median TTFT | Median early start |",
            "|---|---|---|",
        ]
        for arm in data["controller_ablation"]:
            lines.append(
                f"| {arm['arm']} | {arm['median_ttft_ms']} ms | "
                f"{arm['median_early_start_ms']} ms |"
            )
        lines += [
            "",
            "`controller=always_wait` disables speculative retrieval while leaving",
            "every other component identical, which isolates the contribution of",
            "the streaming controller alone.",
        ]

    if data.get("gauntlet"):
        passed = sum(1 for row in data["gauntlet"] if row["passed"])
        lines += [
            "",
            "## 3. Trust Gauntlet (adversarial prompts)",
            "",
            f"**{passed}/{len(data['gauntlet'])} passed.**",
            "",
            "| ID | Kind | Flagged uncertainty | Fabricated IDs | Result |",
            "|---|---|---|---|---|",
        ]
        for row in data["gauntlet"]:
            lines.append(
                f"| {row['id']} | {row['kind']} | "
                f"{'yes' if row['flagged_uncertainty'] else 'no'} | "
                f"{row['fabricated_ids']} | {'PASS' if row['passed'] else 'FAIL'} |"
            )

    lines += [
        "",
        "## 4. How to reproduce",
        "",
        "```bash",
        "python -m corpus.build_index",
        "python -m eval.run_eval",
        "```",
        "",
        "With no `ANTHROPIC_API_KEY` set the run is fully deterministic: the",
        "decomposer uses its clause splitter and synthesis extracts claim text",
        "directly from retrieved chunks, so these numbers reproduce exactly.",
        "Set the key to measure the LLM-backed path instead.",
        "",
    ]
    return "\n".join(lines)


# ---------------- main ----------------

async def main_async(args: argparse.Namespace) -> int:
    rows = load_jsonl(TESTSET)
    if not rows:
        print(f"No test set found at {TESTSET}", file=sys.stderr)
        return 1
    if args.limit:
        rows = rows[: args.limit]

    engine = RetrievalEngine.from_index_file()
    set_engine(engine)
    aegis = AegisPipeline(engine=engine, store=MemorySessionStore())
    naive = NaivePipeline(engine=engine)

    print(f"Running eval on {len(rows)} queries…")
    started = time.perf_counter()

    recall = await measure_recall(aegis, rows, "aegis")
    recall_naive = await measure_recall(naive, rows, "naive")
    ground = await measure_groundedness(aegis, rows, engine, "aegis")
    ground_naive = await measure_groundedness(naive, rows, engine, "naive")
    ttft = await measure_ttft(aegis, naive, rows)
    cost = await measure_cost(aegis, naive)
    gauntlet = await run_gauntlet(aegis, engine)

    ablations: list[dict[str, Any]] = []
    controller_ablation: list[dict[str, Any]] = []
    if not args.quick:
        print("Running ablations…")
        ablations = await run_ablations(rows)
        controller_ablation = await run_controller_ablation(rows)

    from backend.embeddings import get_encoder  # noqa: PLC0415
    from backend.llm import get_client  # noqa: PLC0415

    data = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "env": {
            "embedding_backend": getattr(get_encoder(), "name", "unknown"),
            "llm_provider": get_client().provider,
            "chunks": len(engine.chunks),
            "documents": len({c.doc_id for c in engine.chunks}),
        },
        "recall": recall,
        "recall_naive": recall_naive,
        "groundedness": ground,
        "groundedness_naive": ground_naive,
        "ttft": ttft,
        "cost": cost,
        "gauntlet": gauntlet,
        "ablations": ablations,
        "controller_ablation": controller_ablation,
        "elapsed_s": round(time.perf_counter() - started, 2),
    }

    REPORT.write_text(render_report(data), encoding="utf-8")
    if args.json:
        Path(args.json).write_text(json.dumps(data, indent=2), encoding="utf-8")

    print("\n" + "=" * 62)
    print(f"  Retrieval recall      {recall['overall']:.1%}  "
          f"(naive {recall_naive['overall']:.1%})")
    print(f"    single-intent       {recall['single_intent']:.1%}")
    print(f"    multi-intent        {recall['multi_intent']:.1%}  "
          f"(naive {recall_naive['multi_intent']:.1%})")
    print(f"  Answer groundedness   {ground['groundedness']:.1%}  "
          f"({ground['claims_supported']}/{ground['claims_sampled']} claims)")
    print(f"  Fabricated doc IDs    {ground['fabricated_ids']}")
    print(f"  Median TTFT           {ttft['aegis_median_ttft_ms']} ms  "
          f"(naive {ttft['naive_median_ttft_ms']} ms)")
    print(f"  Refine call reduction {cost['refine_retrieval_call_reduction_pct']}%")
    print(f"  Gauntlet              "
          f"{sum(1 for g in gauntlet if g['passed'])}/{len(gauntlet)} passed")
    print("=" * 62)
    print(f"\nReport written to {REPORT}  ({data['elapsed_s']}s)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Aegis eval harness")
    parser.add_argument("--quick", action="store_true", help="skip ablations")
    parser.add_argument("--limit", type=int, default=0, help="limit test queries")
    parser.add_argument("--json", type=str, default="", help="also write raw JSON here")
    parser.add_argument(
        "--sim-speed", type=float, default=0.12,
        help="replay clock scale for latency measurements (1.0 = true real time)",
    )
    parser.add_argument(
        "--retrieval-latency-ms", type=float, default=0.0,
        help="model a network-attached index; applied to BOTH systems equally",
    )
    args = parser.parse_args()
    config.SIM_SPEED = args.sim_speed
    config.RETRIEVAL_LATENCY_MS = args.retrieval_latency_ms
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
