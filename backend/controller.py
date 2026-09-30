"""[1] Retrieval Controller (PRD §4.1, architecture.md §3.1).

Rule-based by design: cheaper, debuggable, instantly explainable to a jury, and
it runs per-chunk without a model call. The entity extractor is regex+gazetteer
rather than spaCy — one less 500MB dependency for a task that is, at this scale,
"find the proper nouns and the numbers".
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from . import config
from .embeddings import cosine_distance, embed_one
from .schemas import Decision

# Numbers, money, dates, capitalised proper nouns, and quantity phrases.
_NUM_RE = re.compile(r"\b\d+(?:[.,]\d+)?\b")
_MONEY_RE = re.compile(r"[$₹€£]\s?\d[\d,]*(?:\.\d+)?", re.IGNORECASE)
_PROPER_RE = re.compile(r"\b[A-Z][a-zA-Z]{2,}\b")
_END_TOKENS = re.compile(r"[.?!]\s*$")

_STOPWORD_PROPERS = {
    "The",
    "This",
    "That",
    "What",
    "When",
    "Where",
    "How",
    "Why",
    "Who",
    "Can",
    "Could",
    "Would",
    "Should",
    "Please",
    "Also",
    "And",
    "But",
    "For",
    "Actually",
    "Okay",
    "Hey",
    "Hi",
    "Hello",
    "Give",
    "Show",
    "Tell",
    "Make",
    "Need",
    "Want",
    "Let",
    "Are",
    "Does",
    "Did",
    "Have",
    "Has",
    "Book",
    "Find",
    "Our",
    "Their",
    "There",
}

# Slot words that signal a concrete constraint even when lowercase.
_SLOT_HINTS = {
    "people",
    "person",
    "guests",
    "attendees",
    "seats",
    "capacity",
    "budget",
    "days",
    "day",
    "week",
    "weeks",
    "month",
    "months",
    "hours",
    "hour",
    "night",
    "nights",
    "am",
    "pm",
    "quarter",
    "percent",
    "%",
}


def extract_entities(text: str) -> set[str]:
    """Return a normalised entity/slot set. Deterministic and cheap."""
    if not text:
        return set()
    entities: set[str] = set()
    for match in _MONEY_RE.findall(text):
        normalised = re.sub(r"\s+", "", match)
        entities.add(f"money:{normalised}")
    for match in _NUM_RE.findall(text):
        entities.add(f"num:{match}")
    for match in _PROPER_RE.findall(text):
        if match not in _STOPWORD_PROPERS:
            entities.add(f"ent:{match.lower()}")
    lowered = text.lower()
    for hint in _SLOT_HINTS:
        if re.search(rf"\b{re.escape(hint)}\b", lowered):
            entities.add(f"slot:{hint}")
    return entities


def utterance_end_signal(text: str, silence_s: float = 0.0) -> bool:
    """End-of-utterance = terminal punctuation or a silence timeout."""
    if silence_s >= config.SILENCE_TIMEOUT_S:
        return True
    return bool(_END_TOKENS.search(text.strip()))


@dataclass
class ControllerState:
    """Per-session rolling state. Nothing here outlives the session."""

    buffer: str = ""
    entities: set[str] = field(default_factory=set)
    last_provisional_t: float = -999.0
    last_provisional_len: int = 0
    provisional_fired: bool = False
    provisional_entities: set[str] = field(default_factory=set)
    chunk_count: int = 0
    first_chunk_t: Optional[float] = None
    last_chunk_t: float = 0.0

    def reset_turn(self) -> None:
        self.buffer = ""
        self.entities = set()
        self.last_provisional_t = -999.0
        self.last_provisional_len = 0
        self.provisional_fired = False
        self.provisional_entities = set()
        self.chunk_count = 0
        self.first_chunk_t = None


@dataclass
class ControllerDecision:
    decision: Decision
    reason: str
    entities: list[str] = field(default_factory=list)
    entity_growth_rate: float = 0.0
    drift: float = 0.0


def decide(
    state: ControllerState,
    chunk: str,
    t: float,
    silence_s: float = 0.0,
    is_final: bool = False,
) -> ControllerDecision:
    """Fold one transcript chunk into the buffer and return a decision.

    Order of checks matters: an explicit end-of-utterance always wins over the
    speculative path, so we can never sit in PROVISIONAL when the user is done.
    """
    chunk = (chunk or "").strip()
    previous_buffer = state.buffer
    if chunk:
        state.buffer = f"{state.buffer} {chunk}".strip()
        state.chunk_count += 1
        if state.first_chunk_t is None:
            state.first_chunk_t = t
    state.last_chunk_t = t

    entities = extract_entities(state.buffer)
    new_entities = entities - state.entities
    growth = len(new_entities) / max(len(entities), 1)

    drift = 1.0
    if previous_buffer:
        # Semantic volatility between *consecutive chunk states*, per
        # architecture.md §3.1. Comparing the buffer against a fixed-length
        # truncation of itself (an earlier implementation here) is unstable on
        # short buffers: chopping 25 characters off a 30-character utterance
        # compares a sentence to a fragment and reports drift near 1.0 no matter
        # what the speaker said. Consecutive states are what "settling" means.
        drift = cosine_distance(embed_one(state.buffer), embed_one(previous_buffer))

    state.entities = entities
    ent_list = sorted(entities)

    def result(decision: Decision, reason: str) -> ControllerDecision:
        return ControllerDecision(
            decision=decision,
            reason=reason,
            entities=ent_list,
            entity_growth_rate=round(growth, 3),
            drift=round(drift, 4),
        )

    # 1. Terminal state: the utterance is over.
    if is_final or utterance_end_signal(state.buffer, silence_s):
        return result(Decision.RETRIEVE, f"utterance_end; entities={len(entities)}")

    if not state.buffer:
        return result(Decision.WAIT, "empty_buffer")

    # Ablation arm: a controller that never speculates (= the naive baseline's
    # policy). Keeps the ablation honest — same code path, one flag.
    if config.CONTROLLER_MODE == "always_wait":
        return result(Decision.WAIT, "controller_mode=always_wait")

    # 2. Too little transcript to speculate on at all.
    if len(state.buffer) < config.MIN_BUFFER_CHARS_FOR_PROVISIONAL:
        return result(
            Decision.WAIT,
            f"buffer_too_short ({len(state.buffer)} chars) for speculation",
        )

    # 3. Still volatile — entities arriving fast means the query is forming.
    if growth > config.ENTITY_GROWTH_WAIT_THRESHOLD:
        return result(
            Decision.WAIT,
            f"entity_growth_rate={growth:.2f} > "
            f"{config.ENTITY_GROWTH_WAIT_THRESHOLD}",
        )

    # 4. Debounce: never thrash retrieval on consecutive chunks. Two
    #    independent gates, because a single long cooldown is the wrong tool:
    #    it stops thrashing but also stops the controller from ever catching a
    #    late-arriving intent, which is precisely the case full-duplex exists
    #    to handle. So we allow a re-fire as soon as the buffer has grown
    #    materially, and use the time cooldown only as a floor.
    if t - state.last_provisional_t < config.PROVISIONAL_COOLDOWN_S:
        return result(Decision.WAIT, "provisional_cooldown_active")
    if state.provisional_fired:
        growth_chars = len(state.buffer) - state.last_provisional_len

        previous_text = state.buffer[: state.last_provisional_len].strip()
        current_text = state.buffer.strip()

        # Only inspect the newly added portion of the utterance.
        if current_text.startswith(previous_text):
            new_text = current_text[len(previous_text) :].strip()
        else:
            new_text = current_text

        new_words = [word.strip(".,?!:;()[]{}").lower() for word in new_text.split()]

        # Words that commonly introduce a second request.
        intent_connectors = {
            "also",
            "additionally",
            "plus",
            "another",
            "second",
            "and",
        }

        # Request-oriented words are stronger evidence of a new intent
        # than a new location/number/constraint.
        request_words = {
            "what",
            "which",
            "where",
            "when",
            "how",
            "tell",
            "explain",
            "provide",
            "give",
            "show",
            "policy",
            "process",
            "procedure",
            "approval",
            "cancellation",
            "parking",
            "catering",
            "documents",
            "requirements",
            "availability",
        }

        has_connector = any(word in intent_connectors for word in new_words)
        has_request_word = any(word in request_words for word in new_words)

        # A second retrieval is justified when the newly added text
        # looks like a new request/clause rather than just a constraint.
        new_intent_detected = has_connector and has_request_word

        if not new_intent_detected:
            return result(
                Decision.WAIT,
                f"same_intent_growth_{growth_chars}_chars",
            )

    # 5. Speculative fire: entities locked and semantics settling.
    content_words = len([w for w in state.buffer.split() if len(w) > 3])
    stable_enough = (
        len(entities) >= config.MIN_ENTITIES_FOR_PROVISIONAL
        or content_words >= config.MIN_CONTENT_WORDS_FOR_PROVISIONAL
    )
    if stable_enough:

        state.last_provisional_t = t
        state.last_provisional_len = len(state.buffer)
        state.provisional_fired = True
        state.provisional_entities = set(entities)

        locked = (
            ", ".join(e.split(":", 1)[1] for e in ent_list[:4])
            or f"{content_words} content words"
        )
        return result(Decision.PROVISIONAL_RETRIEVE, f"entities_locked: [{locked}]")

    return result(
        Decision.WAIT,
        f"drift={drift:.2f} entities={len(entities)} below provisional bar",
    )
