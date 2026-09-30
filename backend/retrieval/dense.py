"""Dense retrieval over normalised embeddings.

Parsimony note: architecture.md names FAISS. At 15-30 documents (~200 chunks) a
single numpy matmul is exact, faster than a FAISS index build, and removes a
notoriously platform-fragile wheel from the install path. Exact brute-force
search is strictly *more* accurate than an approximate index — we lose nothing
but a dependency. If the corpus ever grows past ~50k chunks, swap this class
for FAISS behind the same two-method interface.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np

from ..embeddings import embed, embed_one
from ..schemas import Chunk


class DenseIndex:
    def __init__(self, chunks: Sequence[Chunk], matrix: np.ndarray | None = None) -> None:
        self.chunks: list[Chunk] = list(chunks)
        if matrix is not None and len(matrix) == len(self.chunks):
            self.matrix = np.asarray(matrix, dtype=np.float32)
        else:
            texts = [f"{c.section}. {c.text}" for c in self.chunks]
            self.matrix = embed(texts).astype(np.float32)
        if self.matrix.size:
            norms = np.linalg.norm(self.matrix, axis=1, keepdims=True)
            self.matrix = self.matrix / np.clip(norms, 1e-9, None)

    def __len__(self) -> int:
        return len(self.chunks)

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        if not self.chunks or self.matrix.size == 0:
            return []
        q = embed_one(query).astype(np.float32)
        norm = float(np.linalg.norm(q))
        if norm < 1e-9:
            return []
        q = q / norm
        if q.shape[0] != self.matrix.shape[1]:
            return []
        sims = self.matrix @ q
        k = min(top_k, len(self.chunks))
        idx = np.argpartition(-sims, k - 1)[:k]
        idx = idx[np.argsort(-sims[idx])]
        return [
            (self.chunks[i].chunk_id, float(sims[i]))
            for i in idx
            if float(sims[i]) > 0.0
        ]
