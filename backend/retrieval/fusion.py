"""Reciprocal Rank Fusion (architecture.md §3.3).

Rank-based, so it fuses BM25 scores and cosine similarities without any score
normalisation step — that scale-invariance is exactly why RRF is the right
"simple beats heavy" choice here.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Sequence

from .. import config


def rrf(
    result_lists: Sequence[Sequence[str]],
    k: int | None = None,
    weights: Sequence[float] | None = None,
) -> list[tuple[str, float]]:
    """Fuse ranked chunk-id lists. Returns [(chunk_id, fused_score)] desc."""
    kk = config.RRF_K if k is None else k
    scores: dict[str, float] = defaultdict(float)
    for list_idx, results in enumerate(result_lists):
        weight = 1.0
        if weights is not None and list_idx < len(weights):
            weight = float(weights[list_idx])
        seen: set[str] = set()
        rank = 0
        for chunk_id in results:
            if chunk_id in seen:  # dedup within a single list
                continue
            seen.add(chunk_id)
            scores[chunk_id] += weight * (1.0 / (kk + rank + 1))
            rank += 1
    return sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))


def ids_only(pairs: Iterable[tuple[str, float]]) -> list[str]:
    return [chunk_id for chunk_id, _ in pairs]
