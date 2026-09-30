"""Central configuration. Every tunable in one place so the ablations in
architecture.md §7 are flag-flips, not code edits."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _env_bool(key: str, default: bool) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, default))
    except (TypeError, ValueError):
        return default


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, default))
    except (TypeError, ValueError):
        return default


ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = Path(os.getenv("AEGIS_CORPUS_DIR", ROOT / "corpus" / "docs"))
INDEX_PATH = Path(os.getenv("AEGIS_INDEX_PATH", ROOT / "corpus" / "index.json"))
RUNLOG_DIR = Path(os.getenv("AEGIS_RUNLOG_DIR", ROOT / "runlogs"))

# --- Controller (architecture.md §3.1) ---
ENTITY_GROWTH_WAIT_THRESHOLD = _env_float("AEGIS_ENTITY_GROWTH_THRESHOLD", 1.00)
DRIFT_THRESHOLD = _env_float("AEGIS_DRIFT_THRESHOLD", 0.45)
MIN_ENTITIES_FOR_PROVISIONAL = _env_int("AEGIS_MIN_ENTITIES", 1)
# The real anti-noise guard: never speculate on a fragment too short to carry a
# retrievable intent. Cheaper and far more predictable than entity counting.
MIN_BUFFER_CHARS_FOR_PROVISIONAL = _env_int("AEGIS_MIN_BUFFER_CHARS", 28)
# Entity-lock is the fast path to "stable", not the only path: plenty of real
# questions carry no proper nouns or numbers at all. A buffer with enough
# content words and low drift is stable too.
MIN_CONTENT_WORDS_FOR_PROVISIONAL = _env_int("AEGIS_MIN_CONTENT_WORDS", 5)
N_LAST_CHARS = _env_int("AEGIS_N_LAST_CHARS", 25)
PROVISIONAL_COOLDOWN_S = _env_float("AEGIS_PROVISIONAL_COOLDOWN_S", 0.3)
# Minimum new transcript (chars) before the controller may speculate again.
PROVISIONAL_MIN_GROWTH_CHARS = _env_int("AEGIS_PROVISIONAL_MIN_GROWTH_CHARS", 12)
# How closely a speculative sub-query must match a final one to be reused.
PROVISIONAL_REUSE_THRESHOLD = _env_float("AEGIS_PROVISIONAL_REUSE_THRESHOLD", 0.75)
SILENCE_TIMEOUT_S = _env_float("AEGIS_SILENCE_TIMEOUT_S", 1.2)

# --- Decomposer (architecture.md §3.2) ---
ORTHOGONALITY_THRESHOLD = _env_float("AEGIS_ORTHOGONALITY_THRESHOLD", 0.85)
MAX_SUB_QUERIES = _env_int("AEGIS_MAX_SUB_QUERIES", 4)

# --- Retrieval / fusion ---
SPARSE_TOP_K = _env_int("AEGIS_SPARSE_TOP_K", 10)
DENSE_TOP_K = _env_int("AEGIS_DENSE_TOP_K", 10)
RRF_K = _env_int("AEGIS_RRF_K", 60)
FUSED_TOP_K = _env_int("AEGIS_FUSED_TOP_K", 8)
FINAL_TOP_K = _env_int("AEGIS_FINAL_TOP_K", 5)
CHUNK_TARGET_WORDS = _env_int("AEGIS_CHUNK_TARGET_WORDS", 90)

# --- Ablation switches (architecture.md §7) ---
USE_SPARSE = _env_bool("AEGIS_USE_SPARSE", True)
USE_DENSE = _env_bool("AEGIS_USE_DENSE", True)
USE_RERANKER = _env_bool("AEGIS_USE_RERANKER", True)
CONTROLLER_MODE = os.getenv("AEGIS_CONTROLLER_MODE", "rule")  # rule | always_wait

# --- Embeddings / LLM providers ---
EMBEDDING_BACKEND = os.getenv("AEGIS_EMBEDDING_BACKEND", "auto")  # auto|local|st
ST_MODEL_NAME = os.getenv("AEGIS_ST_MODEL", "BAAI/bge-small-en-v1.5")
EMBEDDING_DIM = _env_int("AEGIS_EMBEDDING_DIM", 512)

LLM_PROVIDER = os.getenv(
    "AEGIS_LLM_PROVIDER", "auto"
)  # auto|ollama|anthropic|heuristic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
LLM_MODEL = os.getenv("AEGIS_LLM_MODEL", "claude-sonnet-4-6")
LLM_TIMEOUT_S = _env_float("AEGIS_LLM_TIMEOUT_S", 180.0)

# --- Cost model (architecture.md §6.4) ---
USD_PER_1K_INPUT_TOKENS = _env_float("AEGIS_USD_PER_1K_INPUT", 0.003)
USD_PER_1K_OUTPUT_TOKENS = _env_float("AEGIS_USD_PER_1K_OUTPUT", 0.015)
USD_PER_RETRIEVAL_CALL = _env_float("AEGIS_USD_PER_RETRIEVAL", 0.00002)

# --- Streaming realism ---
# When a turn is replayed in real time, transcript chunks are delivered on their
# own timestamps instead of all at once. This is what makes speculative
# retrieval genuinely overlap with speech rather than merely appear to.
# SIM_SPEED scales the replay clock (1.0 = true real time; 0.1 = 10x faster,
# used by the eval harness so a full run stays under a minute).
REALTIME_REPLAY = _env_bool("AEGIS_REALTIME_REPLAY", True)
SIM_SPEED = _env_float("AEGIS_SIM_SPEED", 1.0)
# Models a network-attached index (Elasticsearch/managed vector DB) instead of
# an in-process one. Applied identically to Aegis and the naive baseline, so it
# never biases the comparison. Default 0 = pure local measurement.
RETRIEVAL_LATENCY_MS = _env_float("AEGIS_RETRIEVAL_LATENCY_MS", 0.0)

# --- Session store ---
REDIS_URL = os.getenv("AEGIS_REDIS_URL", "")  # empty => in-process memory store
SESSION_TTL_S = _env_int("AEGIS_SESSION_TTL_S", 1800)
