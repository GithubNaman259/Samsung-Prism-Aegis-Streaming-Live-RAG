"""Retrieval engine: the single object the rest of the pipeline talks to.

Hybrid search (BM25 + dense) → RRF → rerank, with sub-queries dispatched
through asyncio.gather for true parallelism (PRD §4.2).
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Sequence

import numpy as np

from .. import config
from ..schemas import Chunk, ScoredChunk
from . import fusion
from .corpus import build_chunks
from .dense import DenseIndex
from .rerank import rerank as rerank_chunks
from .sparse import BM25Index


@dataclass
class RetrievalResult:
    sub_query: str
    chunks: list[ScoredChunk] = field(default_factory=list)
    calls: int = 0

    @property
    def chunk_ids(self) -> list[str]:
        return [s.chunk.chunk_id for s in self.chunks]


class RetrievalEngine:
    def __init__(self, chunks: Sequence[Chunk], dense_matrix: np.ndarray | None = None) -> None:
        self.chunks: list[Chunk] = list(chunks)
        self.by_id: dict[str, Chunk] = {c.chunk_id: c for c in self.chunks}
        self.sparse = BM25Index(self.chunks)
        self.dense = DenseIndex(self.chunks, dense_matrix)

    # ---------- construction ----------

    @classmethod
    def from_corpus(cls, corpus_dir: Path | None = None) -> "RetrievalEngine":
        return cls(build_chunks(corpus_dir))

    @classmethod
    def from_index_file(cls, path: Path | None = None) -> "RetrievalEngine":
        """Load a prebuilt index; rebuild from the corpus if it is missing or
        stale (dimension mismatch after an embedding-backend switch)."""
        index_path = Path(path or config.INDEX_PATH)
        if index_path.exists():
            try:
                payload = json.loads(index_path.read_text(encoding="utf-8"))
                chunks = [Chunk(**c) for c in payload["chunks"]]
                matrix = np.asarray(payload["embeddings"], dtype=np.float32)
                if len(chunks) == len(matrix) and len(chunks) > 0:
                    return cls(chunks, matrix)
            except Exception:  # noqa: BLE001 - stale index must never be fatal
                pass
        return cls.from_corpus()

    # ---------- search ----------

    def _hybrid_ranked_ids(self, query: str) -> list[str]:
        lists: list[list[str]] = []
        weights: list[float] = []
        if config.USE_SPARSE:
            lists.append([cid for cid, _ in self.sparse.search(query, config.SPARSE_TOP_K)])
            weights.append(1.0)
        if config.USE_DENSE:
            lists.append([cid for cid, _ in self.dense.search(query, config.DENSE_TOP_K)])
            weights.append(1.0)
        if not lists:  # both ablated off — degrade to sparse rather than nothing
            lists.append([cid for cid, _ in self.sparse.search(query, config.SPARSE_TOP_K)])
            weights.append(1.0)
        fused = fusion.rrf(lists, weights=weights)
        return [cid for cid, _ in fused[: config.FUSED_TOP_K]]

    def search_sync(self, query: str, top_k: int | None = None) -> RetrievalResult:
        """One sub-query: hybrid → RRF → rerank. Pure CPU, no I/O."""
        k = top_k or config.FINAL_TOP_K
        query = (query or "").strip()
        if not query:
            return RetrievalResult(sub_query=query, chunks=[], calls=0)
        fused_ids = self._hybrid_ranked_ids(query)
        candidates = [self.by_id[cid] for cid in fused_ids if cid in self.by_id]
        scored = rerank_chunks(query, candidates, k)
        calls = int(config.USE_SPARSE) + int(config.USE_DENSE) or 1
        return RetrievalResult(sub_query=query, chunks=scored, calls=calls)

    async def search(self, query: str, top_k: int | None = None) -> RetrievalResult:
        """Async wrapper — offloaded to a thread so CPU-bound BM25/matmul work
        on several sub-queries genuinely overlaps instead of blocking the loop.

        RETRIEVAL_LATENCY_MS optionally models a network-attached index. It is
        applied here, in the shared path, so both Aegis and the naive baseline
        pay it identically.
        """
        if config.RETRIEVAL_LATENCY_MS > 0:
            await asyncio.sleep(config.RETRIEVAL_LATENCY_MS / 1000.0)
        return await asyncio.to_thread(self.search_sync, query, top_k)

    async def search_many(
        self, queries: Sequence[str], top_k: int | None = None
    ) -> list[RetrievalResult]:
        """Parallel dispatch — architecture.md §2's asyncio.gather step."""
        if not queries:
            return []
        return list(
            await asyncio.gather(*[self.search(q, top_k) for q in queries])
        )

    # ---------- helpers ----------

    def fuse_results(
        self, results: Sequence[RetrievalResult], top_k: int | None = None
    ) -> list[ScoredChunk]:
        """Fuse across sub-query result sets into one deduped evidence list."""
        k = top_k or config.FINAL_TOP_K
        ranked_lists = [r.chunk_ids for r in results if r.chunk_ids]
        if not ranked_lists:
            return []
        fused = fusion.rrf(ranked_lists)
        best_score: dict[str, float] = {}
        for r in results:
            for s in r.chunks:
                cid = s.chunk.chunk_id
                best_score[cid] = max(best_score.get(cid, 0.0), s.score)
        out: list[ScoredChunk] = []
        seen_hashes: set[int] = set()
        for cid, fused_score in fused:
            chunk = self.by_id.get(cid)
            if chunk is None:
                continue
            h = hash(chunk.text)  # dedup by content hash (PRD §4.3)
            if h in seen_hashes:
                continue
            seen_hashes.add(h)
            out.append(
                ScoredChunk(
                    chunk=chunk,
                    score=fused_score + 0.001 * best_score.get(cid, 0.0),
                    source="fused",
                )
            )
            if len(out) >= k:
                break
        return out

    def exists(self, chunk_id: str) -> bool:
        return chunk_id in self.by_id


_engine: Optional[RetrievalEngine] = None


def get_engine() -> RetrievalEngine:
    global _engine
    if _engine is None:
        _engine = RetrievalEngine.from_index_file()
    return _engine


def set_engine(engine: Optional[RetrievalEngine]) -> None:
    global _engine
    _engine = engine
