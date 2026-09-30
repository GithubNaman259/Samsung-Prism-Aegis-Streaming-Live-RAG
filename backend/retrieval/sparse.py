"""BM25 sparse retrieval.

Implemented in ~60 lines of stdlib rather than pulling `rank_bm25`. Same
algorithm, one less dependency to break a judge's `pip install`, and it lets us
expose per-term stats for the demo. This is the "simple and cheap" rule applied
to a dependency decision.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Sequence

from ..embeddings import tokenize
from ..schemas import Chunk


def _bm25_tokens(text: str) -> list[str]:
    """Tokenize with a tiny deterministic plural normalizer.

    The corpus is small and domain-specific; full stemming would add another
    dependency and can distort proper names.  Normalizing only common English
    plural endings fixes high-value lexical mismatches such as
    ``cancellations`` ↔ ``cancellation`` and ``venues`` ↔ ``venue``.
    """
    out: list[str] = []
    for token in tokenize(text):
        if len(token) > 5 and token.endswith("ies"):
            token = token[:-3] + "y"
        elif len(token) > 4 and token.endswith("s") and not token.endswith(("ss", "us")):
            token = token[:-1]
        out.append(token)
    return out


class BM25Index:
    def __init__(self, chunks: Sequence[Chunk], k1: float = 1.5, b: float = 0.75) -> None:
        self.chunks: list[Chunk] = list(chunks)
        self.k1 = k1
        self.b = b
        self._doc_tokens: list[Counter[str]] = []
        self._doc_len: list[int] = []
        doc_freq: Counter[str] = Counter()

        for chunk in self.chunks:
            toks = _bm25_tokens(f"{chunk.doc_id} {chunk.section} {chunk.text}")
            counts = Counter(toks)
            self._doc_tokens.append(counts)
            self._doc_len.append(len(toks))
            doc_freq.update(counts.keys())

        n_docs = max(len(self.chunks), 1)
        self.avg_len = (sum(self._doc_len) / n_docs) if n_docs else 0.0
        # Robertson/Sparck-Jones IDF, floored at a small positive value so
        # ultra-common terms contribute ~0 instead of going negative.
        self.idf: dict[str, float] = {
            term: max(
                math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5)),
                1e-6,
            )
            for term, df in doc_freq.items()
        }

    def __len__(self) -> int:
        return len(self.chunks)

    def score_all(self, query: str) -> list[float]:
        q_terms = _bm25_tokens(query)
        scores = [0.0] * len(self.chunks)
        if not q_terms or not self.chunks:
            return scores
        avg = self.avg_len or 1.0
        for term in q_terms:
            idf = self.idf.get(term)
            if idf is None:
                continue
            for i, counts in enumerate(self._doc_tokens):
                tf = counts.get(term, 0)
                if not tf:
                    continue
                denom = tf + self.k1 * (
                    1.0 - self.b + self.b * (self._doc_len[i] / avg)
                )
                scores[i] += idf * (tf * (self.k1 + 1.0)) / (denom or 1.0)
        return scores

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """Return [(chunk_id, score)] sorted by score desc, zero-scores dropped."""
        scores = self.score_all(query)
        ranked = sorted(
            ((self.chunks[i].chunk_id, s) for i, s in enumerate(scores) if s > 0.0),
            key=lambda pair: (-pair[1], pair[0]),
        )
        return ranked[:top_k]
