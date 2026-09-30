# Aegis — Complete Project Audit, Fixes, and Current State

Date: 2026-09-23

## Scope

This audit covers the project source/configuration/evaluation/frontend/corpus files in the uploaded
`TheMeowfias_Aegis_Live_v2` tree. The ZIP also contains a bundled Windows `.venv` with thousands of
third-party/runtime files; those are dependencies rather than project-owned source and are excluded
from code review and the clean release ZIP.

Project-owned inventory reviewed:

- Backend: controller, decomposer, pipeline, synthesis, LLM abstraction, schemas, config,
  telemetry, session store, suppression, embeddings, and all retrieval modules.
- Corpus generation/indexing plus all 18 corpus documents and the checked-in index.
- Evaluation harness, baseline, testset, gauntlet, and historical benchmark report.
- Frontend HTML/CSS/JS.
- Dockerfile, docker-compose, requirements, pytest configuration, environment examples.
- Demo scripts and existing run logs.
- Existing tests and the supplied debugging/change-log report.

## Intended architecture

The shipped architecture is:

```text
live transcript
    -> streaming controller
    -> speculative retrieval
    -> multi-intent decomposition
    -> query normalization/validation
    -> orthogonality dedup
    -> hybrid BM25 + dense retrieval
    -> RRF + reranking
    -> sub-query-scoped synthesis
    -> claim verification
    -> uncertainty
    -> WebSocket UI / telemetry
```

The most important trust boundary is that evidence for one intent must not validate a different
intent.

---

# 1. Problems found

## P1 — Ollama decomposition could damage the second intent

The progress report correctly identified the central failure:

```text
find a venue to accommodate 30 people in Pune
retrieve the cancellation
```

or worse:

```text
retrieve the cancellation policy for the venue policy for venue in Pune venue Pune Pune
```

The code already contained a first attempt at `contextualize_subqueries()`, but that implementation
could make the exact problem worse: it treated the presence of phrases such as `the venue` as a
reason to append context even when the entity and location were already present.

### Result

Correct LLM output could be transformed into a malformed retrieval query.

### Fixed

`backend/decomposer.py` now has a deterministic normalization/validation stage after LLM JSON
decomposition and before orthogonality dedup.

It now:

- preserves explicit locations;
- preserves the primary entity;
- restores shortened phrases only when the original request explicitly contained them;
- expands `cancellation` to `cancellation policy` only when the original request contained that
  information;
- removes duplicated venue/location context;
- prevents numeric capacity constraints from leaking into unrelated policy queries;
- canonicalizes venue cancellation context;
- de-duplicates identical repaired queries.

Target behavior is now:

```text
find a venue to accommodate 30 people in Pune
retrieve the cancellation policy for the venue in Pune
```

A regression test also feeds a deliberately malformed LLM result:

```text
retrieve the cancellation policy for the venue policy for venue in Pune venue Pune Pune
```

and verifies that it is repaired to the canonical query.

## P2 — Out-of-corpus questions could produce grounded-but-wrong answers

Before the fix,:

```text
What is the parental leave policy?
```

could retrieve a venue/catering chunk containing the generic word `policy` and turn that into a
grounded claim.

This is dangerous because the claim can be factually true in the corpus while still not answering
the user's question.

### Fixed

`backend/synthesis.py` now requires stronger evidence quality in `_query_relevant_chunks()`.

A candidate must still meet the existing retrieval threshold, but it also needs meaningful support:

- at least two meaningful query-term matches, or
- a stronger reranker score, or
- appropriate policy/approval/cancellation evidence with sufficient support.

This keeps the existing recall threshold instead of globally raising it.

### Verified

Both of these now produce no claims and explicit uncertainty:

```text
What is the parental leave policy?
What is the parental leave policy and how many weeks are paid?
```

This directly fixes the two failing tests in the uploaded project.

## P3 — Location hard constraints were too strict for generic policies

The earlier location filter required every evidence chunk for a query such as:

```text
retrieve the cancellation policy for the venue in Pune
```

to literally mention Pune.

The corpus's standard cancellation policy is intentionally generic. Requiring `Pune` in the
policy chunk discarded valid cancellation-policy evidence.

### Fixed

Location handling is now intent-aware:

- venue facts, capacity, rates, accessibility, etc. keep hard location constraints;
- generic policy/approval/cancellation/deadline intents can use corpus-wide policy chunks;
- comparative multi-location requests such as Pune vs Bangalore accept evidence from either region,
  rather than requiring every chunk to mention both cities.

This fixes the retrieval semantics without globally removing location protection.

## P4 — Comparative capacity query could produce an irrelevant claim

For:

```text
Compare venue capacity in Pune and Bangalore and tell me the rate difference between regions
```

the old location filter could discard the actual Pune/Bangalore venue chunks because no single
chunk necessarily mentions both cities. A generic per-diem chunk that mentioned both cities could
then become the surviving evidence.

### Fixed

Comparative queries can retrieve one regional evidence chunk per location.

Additionally, `_best_sentence()` now applies lightweight intent-field focus. For example:

- `capacity` prefers `seats/accommodate/people` sentences;
- `rate/cost/fee` prefers pricing sentences;
- `cancellation/policy` prefers cancellation-policy sentences;
- `catering` prefers catering/menu/service sentences;
- approval/deadline/accessibility/equipment terms receive similar focus.

The capacity claim now comes from the actual venue-capacity sentence rather than the unrelated
per-diem sentence.

## P5 — Sparse retrieval had avoidable plural mismatches

The corpus uses forms such as:

```text
Cancellations ...
```

while user queries may use:

```text
cancellation ...
```

The dense encoder partially handles this through character n-grams, but the sparse BM25 path did not.

### Fixed

`backend/retrieval/sparse.py` now uses a tiny deterministic plural normalizer for BM25 tokens.

It intentionally avoids full stemming and only normalizes common plural endings. This improves
lexical matching such as:

```text
cancellations <-> cancellation
venues <-> venue
```

without adding another dependency.

---

# 2. Existing changes retained

The supplied progress report identified several changes that were already correct. They were kept:

- `MIN_RESULT_RELEVANCE_SCORE = 0.30`
- `MIN_QUERY_TERM_OVERLAP = 0.35`
- sub-query-scoped claim verification
- sub-query-scoped coverage
- evidence-boundary rules in the LLM synthesis prompt
- explicit constraint enforcement in the synthesis prompt
- heuristic grounded claim fallback
- preservation of provisional/speculative evidence
- refine-vs-new-topic path
- stronger LLM decomposition prompt
- strengthened heuristic decomposition

The retrieval thresholds were not globally raised as a shortcut.

---

# 3. Current tests

After the fixes:

```text
53 passed
0 failed
```

Python bytecode compilation also succeeds for backend, corpus, eval, and tests.

The important trust checks pass:

- out-of-corpus parental-leave query -> uncertainty, no claim;
- ambiguous late cancellation -> uncertainty;
- reschedule/catering contradiction -> grounded answer;
- false Riverside Studio capacity premise -> contradiction is surfaced through the corpus;
- no fabricated chunk IDs;
- LLM normalization regression -> canonical sub-queries;
- all existing pipeline tests -> pass.

---

# 4. Current exact decomposition contract

For:

```text
find a venue to accommodate 30 people in Pune and retrieve the cancellation policy for the venue in Pune
```

the LLM path is now expected to dispatch:

```text
find a venue to accommodate 30 people in Pune
retrieve the cancellation policy for the venue in Pune
```

The normalization layer is deterministic, so a weak Ollama response cannot directly poison retrieval.

---

# 5. Important distinction: retrieval correctness vs claim responsiveness

The project still has two separate concepts:

### Retrieval

Did the system retrieve evidence relevant to the requested intent?

### Responsiveness

Did the final claim actually answer that intent?

The fixes now reinforce both boundaries.

A claim can no longer become acceptable merely because it is grounded in a real chunk if that chunk
only shares a generic word with the query.

---

# 6. Historical report discrepancy

The supplied `Aegis_RAG_Debugging_Change_Log_and_Next_Steps.md` says that LLM sub-query
normalization was "not implemented yet".

That is no longer literally true in the uploaded codebase: an earlier, incomplete implementation
was already present in `backend/decomposer.py`.

The important finding is that the existing implementation was not sufficient. The current fix
replaces it with a stricter normalization/validation implementation and adds regression tests.

The historical benchmark report also predates these fixes and should be treated as a historical
snapshot, not as the post-fix benchmark.

---

# 7. Evaluation caveat

The full `eval/run_eval.py` latency benchmark intentionally forces real-time replay for TTFT.
That is why a full benchmark can take substantially longer than the unit-test suite.

I did not rewrite the benchmark to manufacture a faster number.

The post-fix correctness checks were run with realtime disabled so they test decomposition,
retrieval, synthesis, grounding, and uncertainty without waiting for speech replay.

---

# 8. Packaging problem found

The uploaded ZIP contains approximately 5,000 files, including a bundled Windows `.venv`,
compiled `.pyc` files, third-party packages, and other runtime artifacts.

Those files are not part of the application source and make the project unnecessarily large.

The clean release should exclude:

```text
.venv/
__pycache__/
*.pyc
.pytest_cache/
.git/
```

The release ZIP generated with this audit follows that rule while retaining the application,
corpus, tests, evaluation harness, configuration, and demo material.

---

# 9. Configuration consistency fix

The uploaded working `.env` uses:

```text
AEGIS_OLLAMA_MODEL=qwen3:1.7b
```

but the README and `.env.example` previously described Qwen3 4B.

The project now defaults/documentates the lighter:

```text
qwen3:1.7b
```

The model remains configurable through `AEGIS_OLLAMA_MODEL`.

This matches the current working configuration rather than silently documenting a different model.

---

# 10. Remaining engineering work

These are not blockers for the fixes above, but they are the next things to address if the goal is
to push the project beyond the current hackathon-ready state.

### R1 — Run the complete post-fix benchmark

The full benchmark should be run on the actual target machine/model, especially with:

```text
AEGIS_LLM_PROVIDER=ollama
AEGIS_OLLAMA_MODEL=qwen3:1.7b
```

The reason is that unit tests can validate the normalization boundary, but only a real Ollama run
can measure the model's actual decomposition behavior and synthesis quality.

### R2 — Re-measure multi-intent recall

The historical snapshot reported approximately 91% overall recall and 78.8% multi-intent recall.
The post-fix pipeline changes should be measured rather than assuming improvement.

### R3 — Improve final evidence budgeting

`FINAL_TOP_K` is currently 5. In compound questions, a valid lower-ranked chunk can be pushed out
of the final fused evidence pool even when its sub-query retrieved it.

A future change should preserve per-sub-query evidence quotas before global fusion, rather than
blindly increasing `FINAL_TOP_K`.

### R4 — Expand regression matrix

The next tests should cover:

- Pune/Bangalore variants;
- Bengaluru spelling;
- hotels/restaurants/events;
- multiple numeric constraints;
- dates;
- "that venue"/"the booking"/"it" references;
- more than two intents;
- policy + location combinations;
- comparative two-location queries;
- LLM outputs with duplicate clauses;
- LLM outputs containing extra prose.

### R5 — Keep performance optimization last

Correctness should remain ahead of:

- TTFT;
- retrieval call count;
- token usage;
- estimated cost.

---

# 11. Release acceptance criteria

Before final submission, the project should satisfy:

- [x] LLM-generated secondary sub-query cannot silently lose location/entity context.
- [x] Duplicate LLM context is normalized.
- [x] Numeric capacity constraints are not leaked into policy queries.
- [x] Out-of-corpus requests decline with uncertainty.
- [x] Grounded-but-irrelevant chunks do not automatically become claims.
- [x] Generic policy evidence is allowed without requiring a city string.
- [x] Comparative regional retrieval can use separate regional chunks.
- [x] Capacity claims prefer capacity sentences.
- [x] Existing 53-test suite passes.
- [x] No fabricated chunk IDs.
- [x] Clean release excludes the bundled virtual environment.
- [ ] Full post-fix Ollama benchmark still needs to be run on the target environment.
- [ ] Final multi-intent recall/TTFT/cost numbers should be regenerated after the fixes.

---

# 12. Bottom line

The core problem was not simply "retrieval is weak."

The failure chain was:

```text
Ollama decomposition
      ↓
malformed / context-damaged sub-query
      ↓
wrong retrieval evidence
      ↓
grounded but non-responsive claim
      ↓
uncertainty either too late or not triggered
```

The current fix inserts deterministic validation at the correct boundary:

```text
Ollama decomposition
      ↓
NORMALIZE + VALIDATE
      ↓
dedup
      ↓
retrieval
      ↓
intent-aware evidence filtering
      ↓
intent-focused claim extraction
      ↓
claim verification
      ↓
uncertainty
```

That is the intended direction for Aegis: the LLM can propose structure, but deterministic
normalization, retrieval constraints, evidence boundaries, and verification remain in control.
