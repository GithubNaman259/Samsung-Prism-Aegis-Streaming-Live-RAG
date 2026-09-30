"""Embedding layer.

Parsimony note (architecture.md §11): the default backend is a deterministic,
pure-numpy hashed character+word n-gram encoder. For a 15-30 document corpus it
gives usable semantic similarity with *zero* model download, no torch, no GPU,
and no cold-start — which is what makes `docker compose up` work on a clean
machine. If sentence-transformers is installed and AEGIS_EMBEDDING_BACKEND=st,
we transparently upgrade to bge-small. Nothing else in the codebase changes.
"""
from __future__ import annotations

import hashlib
import math
import re
from functools import lru_cache
from typing import Iterable, Sequence

import numpy as np

from . import config

_WORD_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


class HashingEncoder:
    """Deterministic hashed n-gram encoder producing L2-normalised vectors."""

    name = "hashing-ngram"

    def __init__(self, dim: int = config.EMBEDDING_DIM) -> None:
        self.dim = dim

    def _features(self, text: str) -> Iterable[tuple[str, float]]:
        tokens = tokenize(text)
        if not tokens:
            return []
        feats: list[tuple[str, float]] = []
        for tok in tokens:
            feats.append((f"w:{tok}", 1.0))
            # character 4-grams give partial-word robustness ("cancellation"~"cancel")
            padded = f"^{tok}$"
            for i in range(len(padded) - 3):
                feats.append((f"c:{padded[i:i + 4]}", 0.45))
        for a, b in zip(tokens, tokens[1:]):
            feats.append((f"b:{a}_{b}", 0.8))
        return feats

    def _bucket(self, feature: str) -> tuple[int, float]:
        digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest, "big")
        sign = 1.0 if (value >> 63) & 1 else -1.0
        return value % self.dim, sign

    def encode_one(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float32)
        for feature, weight in self._features(text):
            idx, sign = self._bucket(feature)
            # sublinear damping keeps long chunks from dominating
            vec[idx] += sign * weight
        norm = float(np.linalg.norm(vec))
        if norm < 1e-9:
            return vec
        return vec / norm

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        return np.vstack([self.encode_one(t) for t in texts])


class SentenceTransformerEncoder:
    """Optional upgrade path. Only constructed if the package is importable."""

    name = "sentence-transformers"

    def __init__(self, model_name: str = config.ST_MODEL_NAME) -> None:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415

        self._model = SentenceTransformer(model_name)
        self.dim = int(self._model.get_sentence_embedding_dimension())

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        return np.asarray(
            self._model.encode(list(texts), normalize_embeddings=True),
            dtype=np.float32,
        )

    def encode_one(self, text: str) -> np.ndarray:
        return self.encode([text])[0]


_encoder = None


def get_encoder():
    """Singleton encoder. Falls back to the hashing encoder on any failure so a
    missing/broken model download can never take the demo down."""
    global _encoder
    if _encoder is not None:
        return _encoder
    backend = config.EMBEDDING_BACKEND.lower()
    if backend in {"st", "sentence-transformers", "auto"}:
        try:
            _encoder = SentenceTransformerEncoder()
            return _encoder
        except Exception:  # noqa: BLE001 - deliberate: never fail closed
            if backend != "auto":
                pass
    _encoder = HashingEncoder()
    return _encoder


def embed(texts: Sequence[str]) -> np.ndarray:
    return get_encoder().encode(list(texts))


@lru_cache(maxsize=4096)
def _embed_one_cached(text: str) -> tuple[float, ...]:
    return tuple(float(x) for x in get_encoder().encode_one(text))


def embed_one(text: str) -> np.ndarray:
    return np.asarray(_embed_one_cached(text), dtype=np.float32)


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    return 1.0 - cosine_sim(a, b)


def reset_encoder() -> None:
    """Test hook."""
    global _encoder
    _encoder = None
    _embed_one_cached.cache_clear()


__all__ = [
    "HashingEncoder",
    "SentenceTransformerEncoder",
    "cosine_distance",
    "cosine_sim",
    "embed",
    "embed_one",
    "get_encoder",
    "reset_encoder",
    "tokenize",
    "math",
]
