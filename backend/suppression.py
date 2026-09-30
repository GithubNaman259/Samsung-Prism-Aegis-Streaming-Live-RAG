"""[4.5] Query suppression for presentation-only turns (PRD §4.5).

"Shorten that", "translate it to Hindi", "make it a bullet list" — these need
zero retrieval. Catching them is the cheapest win in the whole system: it turns
a full pipeline turn into a string transform, which shows up directly in the
cost-per-turn metric.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_TRANSFORM_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("presentation_shorten", re.compile(
        r"\b(shorter|shorten|summari[sz]e|summary|tl;?dr|condense|brief(?:er)?|"
        r"cut it down|trim (?:that|it|this))\b", re.IGNORECASE)),
    ("presentation_restructure", re.compile(
        r"\b(bullet(?:s| point.*)?|numbered list|as a list|as a table|"
        r"format|reformat|restructure|rewrite)\b",
        re.IGNORECASE)),
    ("presentation_translate", re.compile(
        r"\b(translate|in (?:hindi|spanish|french|german|punjabi|japanese|"
        r"chinese|tamil|marathi))\b", re.IGNORECASE)),
    ("presentation_tone", re.compile(
        r"\b(formal|simpler|simplify|plain english|"
        r"casual|professional tone|explain it like)\b", re.IGNORECASE)),
    ("presentation_repeat", re.compile(
        r"^\s*(say that again|repeat that|read it back|show (?:that|it) again)\b",
        re.IGNORECASE)),
]

# A turn that introduces new facts is never presentation-only, even if it also
# contains a formatting verb ("make it shorter and add the Pune venue").
_NEW_INFO = re.compile(
    r"\b(what|which|when|where|who|why|how much|how many|cost|price|policy|"
    r"deadline|capacity|rule|available|instead of|add\b.*\b(info|detail|section))\b",
    re.IGNORECASE,
)


@dataclass
class SuppressionResult:
    is_presentation_only: bool
    reason: str
    transform: str = ""


def classify(utterance: str, has_session_state: bool) -> SuppressionResult:
    text = (utterance or "").strip()
    if not text:
        return SuppressionResult(False, "empty_utterance")
    if not has_session_state:
        # Nothing to reformat yet, so it must be a real information request.
        return SuppressionResult(False, "no_prior_answer_to_transform")

    matched: list[tuple[str, str]] = []
    for label, pattern in _TRANSFORM_PATTERNS:
        m = pattern.search(text)
        if m:
            matched.append((label, m.group(0)))
    if not matched:
        return SuppressionResult(False, "no_transform_intent_detected")
    if _NEW_INFO.search(text):
        return SuppressionResult(
            False, "transform_verb_present_but_new_information_requested"
        )
    label, span = matched[0]
    return SuppressionResult(True, f"{label}: matched '{span.lower()}'", label)
