"""[2] Multi-Intent Decomposer (PRD §4.2, architecture.md §3.2).

One structured-output call, never a multi-turn planning loop. When no LLM key is
present a deterministic clause-splitter takes over so the behaviour — and the
eval numbers — are identical on a clean machine.
"""

from __future__ import annotations

import re
from typing import Optional

from . import config
from .embeddings import cosine_sim, embed_one
from .llm import LLMClient, Usage, get_client
from .schemas import SubQuery

SYSTEM = (
    "You split a spoken request into the independent search queries it implies. "
    "Return ONLY JSON, no prose, no markdown fences."
)

PROMPT = """Split the request below into 1-{max_n} independent search queries.

Rules:
- Each sub-query must represent one distinct information need.
- Each sub-query must be independently understandable when shown to a retriever.
- NEVER create a fragment that depends on another sub-query for its subject,
  object, location, entity, date, quantity, or other constraint.
- Every sub-query MUST preserve all context required to answer that intent.
- Preserve named entities and locations such as Pune, Bangalore, Mumbai, etc.
- Preserve explicit numeric constraints such as 30 people.
- Preserve the entity being discussed across multiple intents.
- If a later intent refers to "the venue", "that venue", "it", "the booking",
  "the hotel", "the event", etc., repeat the actual entity/context in that
  sub-query instead of using the pronoun or dropping the context.
- Example:
  Request: "Find a venue to accommodate 30 people in Pune and retrieve the
  cancellation policy for the venue in Pune."
  Correct:
  [
    "find a venue to accommodate 30 people in Pune",
    "retrieve the cancellation policy for the venue in Pune"
  ]
  Incorrect:
  [
    "find a venue to accommodate 30 people in Pune",
    "retrieve the cancellation"
  ]
- Do NOT invent information that is not present in the request.
- If the request implies only one information need, return exactly one item.

Request: "{utterance}"

Respond with: {{"sub_queries": ["...", "..."]}}"""

# Clause boundaries that reliably separate distinct information needs in speech.
_SPLIT_RE = re.compile(
    r"\s*(?:,\s*and\s+|\s+and\s+also\s+|\s+and\s+|;\s*|\s+also\s+|\s+plus\s+"
    r"|\s+as\s+well\s+as\s+|\?\s*)",
    re.IGNORECASE,
)
_LEAD_RE = re.compile(
    r"^(?:hey|hi|hello|okay|ok|so|um|uh|well|please|could you|can you|i need|"
    r"i want|i'd like|tell me|show me|find me|give me|what about|how about)\s+",
    re.IGNORECASE,
)
_FILLER_RE = re.compile(r"\s+")


def _clean(text: str) -> str:
    text = _FILLER_RE.sub(" ", (text or "").strip())
    prev = None
    while prev != text:  # strip stacked lead-ins ("okay so can you ...")
        prev = text
        text = _LEAD_RE.sub("", text).strip()
    return text.strip(" ,.;")


def heuristic_decompose(utterance: str, max_n: int | None = None) -> list[str]:
    """Deterministic clause splitter used when no LLM is configured."""
    limit = max_n or config.MAX_SUB_QUERIES
    cleaned = _clean(utterance)
    if not cleaned:
        return []
    parts = [p.strip(" ,.;") for p in _SPLIT_RE.split(cleaned) if p and p.strip(" ,.;")]
    # Fragments shorter than 3 words are usually continuations, not intents;
    # glue them back onto the previous part instead of firing a junk query.
    merged: list[str] = []
    for part in parts:
        if merged and len(part.split()) < 3:
            merged[-1] = f"{merged[-1]} {part}"
        else:
            merged.append(part)
    if not merged:
        merged = [cleaned]

    cleaned_parts = [_clean(part) or part for part in merged[:limit]]

    if len(cleaned_parts) <= 1:
        return cleaned_parts

    # Preserve context for later intents. A later clause such as
    # "retrieve the cancellation policy" is not independently searchable
    # unless the entity/location from the original request is retained.
    #
    # We deliberately copy only explicit context already present in the
    # original request; we never invent missing information.

    original_terms = cleaned.split()

    # Explicit locations/entities that occur in the original request.
    context_terms: list[str] = []

    for i, token in enumerate(original_terms):
        clean_token = re.sub(r"[^A-Za-z0-9%.-]", "", token)

        if not clean_token:
            continue

        # Preserve known locations/entities.
        if clean_token.lower() in {
            "pune",
            "bangalore",
            "mumbai",
            "delhi",
            "hyderabad",
            "chennai",
            "kolkata",
        }:
            context_terms.append(clean_token)

    # Preserve the primary entity introduced by the first intent.
    entity_terms: list[str] = []

    first = cleaned_parts[0].lower()

    if "venue" in first:
        entity_terms.append("venue")
    elif "hotel" in first:
        entity_terms.append("hotel")
    elif "restaurant" in first:
        entity_terms.append("restaurant")
    elif "event" in first:
        entity_terms.append("event")
    elif "booking" in first:
        entity_terms.append("booking")

    context_suffix = " ".join(entity_terms + context_terms)

    contextualized: list[str] = [cleaned_parts[0]]

    for part in cleaned_parts[1:]:
        lower = part.lower()

        has_entity_here = bool(
            entity_terms and re.search(rf"\b{re.escape(entity_terms[0])}\b", lower)
        )
        has_location_here = not context_terms or any(
            re.search(rf"\b{re.escape(term.lower())}\b", lower)
            for term in context_terms
        )
        needs_context = not has_entity_here or not has_location_here

        if needs_context and context_suffix:
            part = f"{part} {context_suffix}"

        contextualized.append(_clean(part) or part)

    return contextualized


def split_concatenated_subqueries(
    utterance: str,
    sub_queries: list[str],
    max_n: int | None = None,
) -> list[str]:
    """Repair an Ollama response where multiple intents were concatenated.

    Small local models sometimes return one string such as:
        "find a venue ... in Puneretrieve the cancellation policy ..."

    The original utterance is authoritative for the intended clause boundary,
    so when this pattern is detected we reuse the deterministic clause splitter
    rather than trying to invent a new intent from the malformed LLM string.
    """
    if len(sub_queries) != 1:
        return sub_queries

    original = _clean(utterance)
    candidate = _clean(sub_queries[0])

    if not original or not candidate:
        return sub_queries

    # We only activate this repair for a strong, explicit second intent.
    has_policy_intent = bool(
        re.search(
            r"\b(?:and\s+)?(?:retrieve|tell me|give me|show me|get|find)\s+"
            r"(?:the\s+)?cancellation\s+policy\b",
            original,
            flags=re.IGNORECASE,
        )
    )
    if not has_policy_intent:
        return sub_queries

    # The strongest signal is that the malformed model output contains the
    # second intent glued directly onto the first clause (e.g. Puneretrieve).
    glued = re.search(
        r"(?:retrieve|tell me|give me|show me|get|find)\s+"
        r"(?:the\s+)?cancellation\s+policy\b",
        candidate,
        flags=re.IGNORECASE,
    )
    if not glued:
        return sub_queries

    repaired = heuristic_decompose(original, max_n=max_n)
    if len(repaired) >= 2:
        return repaired[: max_n or config.MAX_SUB_QUERIES]

    # Conservative fallback: split the malformed output at the second intent
    # and reconstruct the second query from the original request's location.
    first = _clean(candidate[: glued.start()])
    second = _clean(candidate[glued.start() :])
    if first and second:
        return [first, second]

    return sub_queries


def contextualize_subqueries(utterance: str, sub_queries: list[str]) -> list[str]:
    """Repair missing context in LLM-generated sub-queries."""
    if not sub_queries:
        return []
        
    known_locations = {"pune", "bangalore", "bengaluru", "mumbai", "delhi", "hyderabad", "chennai", "kolkata"}
    entity_patterns = (
        ("venue", r"\bvenue\b"), 
        ("hotel", r"\bhotel\b"), 
        ("restaurant", r"\brestaurant\b"), 
        ("event", r"\bevent\b"), 
        ("booking", r"\bbooking\b")
    )
    
    orig_lower = utterance.lower()
    locations = []
    for token in utterance.split():
        clean_token = re.sub(r"[^a-z0-9]", "", token.lower())
        if clean_token in known_locations and clean_token not in locations:
            locations.append(clean_token)
            
    entity = None
    for name, pattern in entity_patterns:
        if re.search(pattern, orig_lower):
            entity = name
            break
            
    normalized = []
    for idx, sq in enumerate(sub_queries):
        sq = sq.strip()
        lower = sq.lower()
        
        # Canonicalize cancellation intent before appending context
        if idx > 0 and "cancellation" in lower and entity == "venue":
            sq = "retrieve the cancellation policy for the venue"
            if locations:
                sq += f" in {' and '.join(locations)}"
        elif idx > 0:
            # Drop capacity from subsequent sub-queries
            sq = re.sub(r"\b(?:for|of|with)\s+\d+\s+people\b", "", sq, flags=re.IGNORECASE).strip()
            sq = re.sub(r"\b\d+\s+people\b", "", sq, flags=re.IGNORECASE).strip()
            
            # Canonicalize references
            has_ent = entity and re.search(rf"\b{entity}\b", lower)
            has_loc = not locations or any(l in lower for l in locations)
            
            if entity and not has_ent:
                sq += f" {entity}"
            if locations and not has_loc:
                sq += f" in {' and '.join(locations)}"
                
        normalized.append(re.sub(r"\s+", " ", sq).strip())
        
    return normalized


def dedup_subqueries(
    sub_queries: list[str], threshold: float | None = None
) -> list[str]:
    """Orthogonality guard (architecture.md §3.2) — defeats over-fragmentation."""
    limit = config.ORTHOGONALITY_THRESHOLD if threshold is None else threshold
    kept: list[str] = []
    kept_vecs = []
    for sq in sub_queries:
        sq = (sq or "").strip()
        if not sq:
            continue
        vec = embed_one(sq)
        if all(cosine_sim(vec, kv) < limit for kv in kept_vecs):
            kept.append(sq)
            kept_vecs.append(vec)
    return kept


async def decompose(
    utterance: str,
    client: Optional[LLMClient] = None,
    max_n: int | None = None,
) -> tuple[list[SubQuery], Usage]:
    """Return orthogonal sub-queries plus the token usage they cost."""
    limit = max_n or config.MAX_SUB_QUERIES
    llm = client or get_client()
    usage = Usage()
    raw: list[str] = []

    if not llm.is_stub:
        parsed, call_usage = await llm.complete_json(
            SYSTEM,
            PROMPT.format(max_n=limit, utterance=utterance.strip()),
            max_tokens=300,
        )
        usage.add(call_usage)
        if isinstance(parsed, dict):
            candidate = parsed.get("sub_queries")
            if isinstance(candidate, list):
                raw = [str(x) for x in candidate if str(x).strip()]
        elif isinstance(parsed, list):
            raw = [str(x) for x in parsed if str(x).strip()]

    if not raw:  # stub provider, or the model returned nothing usable
        raw = heuristic_decompose(utterance, limit)

    # The LLM may return multiple intents concatenated into one malformed
    # string. Repair that boundary from the original utterance before adding
    # entity/location context.
    raw = split_concatenated_subqueries(utterance, raw, limit)

    # Repair missing entity/location context deterministically before retrieval.
    # raw = contextualize_subqueries(utterance, raw)

    deduped = dedup_subqueries(raw)[:limit]
    if not deduped:
        fallback = _clean(utterance) or (utterance or "").strip()
        deduped = [fallback] if fallback else []
    return [SubQuery(text=t) for t in deduped], usage


# ---------------- refine vs. new-topic (architecture.md §3.4) ----------------

_REFINE_MARKERS = re.compile(
    r"\b(actually|instead|make (?:that|it)|change (?:that|it)|wait|"
    r"sorry|scratch that|correction|rather|no,|update that|also make|"
    r"and make (?:that|it)|i meant)\b",
    re.IGNORECASE,
)
_ELLIPSIS_MARKERS = re.compile(
    r"^(?:and|but|also|plus|with|without|for|in|at|on|make|change|add|remove)\b",
    re.IGNORECASE,
)


def is_refine_turn(
    new_utterance: str, prior_utterance: str, prior_claims: list[str]
) -> tuple[bool, str]:
    """Cheap heuristic first (architecture.md §3.4): explicit correction markers,
    then ellipsis + topical similarity to the existing answer state."""
    text = (new_utterance or "").strip()
    if not text or not prior_claims:
        return False, "no_prior_state"
    if _REFINE_MARKERS.search(text):
        return True, "correction_marker_detected"

    vec = embed_one(text)
    claim_sims = [cosine_sim(vec, embed_one(c)) for c in prior_claims]
    top_sim = max(claim_sims) if claim_sims else 0.0
    prior_sim = cosine_sim(vec, embed_one(prior_utterance)) if prior_utterance else 0.0
    topical = max(top_sim, prior_sim)

    # Do not let the lightweight hashed embedding alone turn an unrelated
    # question into a refine. Generic words such as "policy", "event", or
    # "people" can produce deceptively high similarity. A refinement without
    # an explicit correction marker must share meaningful content terms with
    # the previous turn.
    def terms(value: str) -> set[str]:
        return {
            t
            for t in re.findall(r"[a-z0-9]+", (value or "").lower())
            if len(t) >= 4
            and t
            not in {
                "what",
                "when",
                "where",
                "which",
                "this",
                "that",
                "with",
                "from",
                "about",
                "make",
                "need",
                "want",
                "know",
            }
        }

    new_terms = terms(text)
    prior_terms = terms(prior_utterance) | {t for c in prior_claims for t in terms(c)}
    lexical_overlap = len(new_terms & prior_terms) / max(len(new_terms), 1)

    if _ELLIPSIS_MARKERS.match(text) and topical > 0.20 and lexical_overlap >= 0.25:
        return True, f"ellipsis+topic={topical:.2f}+lexical={lexical_overlap:.2f}"
    return False, f"new_topic; topic={topical:.2f}+lexical={lexical_overlap:.2f}"
