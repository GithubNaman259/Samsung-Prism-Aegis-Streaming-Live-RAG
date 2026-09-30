"""Reranking stage — deliberately toggleable (AEGIS_USE_RERANKER) because
architecture.md §7 requires us to report whether it earns its latency.

Default reranker is a lightweight lexical+semantic scorer: query-term coverage
(recall of query terms inside the chunk) blended with embedding cosine. It runs
in microseconds on CPU. If `sentence_transformers` is available we upgrade to a
real bge cross-encoder; the interface is identical either way.
"""
from __future__ import annotations

from typing import Optional, Sequence

from .. import config
from ..embeddings import cosine_sim, embed_one, tokenize
from ..schemas import Chunk, ScoredChunk


class LexicalSemanticReranker:
    name = "lexical-semantic"

    def score(self, query: str, chunk: Chunk) -> float:
        q_terms = set(tokenize(query))
        if not q_terms:
            return 0.0
        c_terms = set(tokenize(f"{chunk.section} {chunk.text}"))
        coverage = len(q_terms & c_terms) / len(q_terms)
        semantic = cosine_sim(
            embed_one(query), embed_one(f"{chunk.section}. {chunk.text}")
        )
        return 0.6 * coverage + 0.4 * max(semantic, 0.0)

    def rerank(self, query: str, chunks: Sequence[Chunk], top_k: int) -> list[ScoredChunk]:
        scored = [
            ScoredChunk(chunk=c, score=self.score(query, c), source="reranked")
            for c in chunks
        ]
        scored.sort(key=lambda s: (-s.score, s.chunk.chunk_id))
        return scored[:top_k]


class CrossEncoderReranker:
    name = "cross-encoder"

    def __init__(self, model_name: str = "BAAI/bge-reranker-base") -> None:
        from sentence_transformers import CrossEncoder  # noqa: PLC0415

        self._model = CrossEncoder(model_name)

    def rerank(self, query: str, chunks: Sequence[Chunk], top_k: int) -> list[ScoredChunk]:
        if not chunks:
            return []
        pairs = [(query, c.text) for c in chunks]
        raw = self._model.predict(pairs)
        scored = [
            ScoredChunk(chunk=c, score=float(s), source="reranked")
            for c, s in zip(chunks, raw)
        ]
        scored.sort(key=lambda s: (-s.score, s.chunk.chunk_id))
        return scored[:top_k]


_reranker: Optional[object] = None


def get_reranker():
    global _reranker
    if _reranker is not None:
        return _reranker
    if config.EMBEDDING_BACKEND.lower() in {"st", "sentence-transformers"}:
        try:
            _reranker = CrossEncoderReranker()
            return _reranker
        except Exception:  # noqa: BLE001
            pass
    _reranker = LexicalSemanticReranker()
    return _reranker


def rerank(query: str, chunks: Sequence[Chunk], top_k: int) -> list[ScoredChunk]:
    """Rerank, or pass through in original fused order if the stage is off."""
    if not config.USE_RERANKER:
        return [
            ScoredChunk(chunk=c, score=1.0 / (i + 1), source="fused")
            for i, c in enumerate(list(chunks)[:top_k])
        ]
    return get_reranker().rerank(query, chunks, top_k)


def reset_reranker() -> None:
    global _reranker
    _reranker = None
