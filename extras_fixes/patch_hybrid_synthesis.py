import re
with open('aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad = '''    needs_deterministic_grounding = any(
        _is_venue_capacity_query(q) or _is_cancellation_query(q)
        for q in priority_queries
    )

    claim_specs = []
    uncertainty_acc = []
    if not needs_deterministic_grounding:
        for sq_ev in sub_query_evidence:
            out = await _llm_claims(utterance, [sq_ev], llm, usage)
            if out:
                claim_specs.extend(out[0])
                uncertainty_acc.extend(out[1])
        llm_out = (claim_specs, uncertainty_acc) if (claim_specs or uncertainty_acc) else None
    else:
        llm_out = None
    if llm_out is not None:
        claim_specs, uncertainty = llm_out

        # Build a lookup from ALL evidence belonging to each sub-query.
        by_id: dict[str, ScoredChunk] = {}
        for _, sub_evidence in sub_query_evidence:
            for scored in sub_evidence:
                by_id[scored.chunk.chunk_id] = scored

        for text, ids in claim_specs:
            valid_ids = [i for i in ids if i in by_id]

            if not valid_ids:
                continue

            cands = [by_id[i] for i in valid_ids]
            drafts.append((text, cands[:3]))

        # Safety fallback:
        # If the LLM produced no usable grounded claims, recover claims
        # directly from the retrieved evidence instead of returning an empty
        # answer.
        if not drafts:
            fallback_drafts, fallback_uncertainty = heuristic_claims(
                relevant_results, engine
            )
            drafts.extend(fallback_drafts)
            uncertainty.extend(fallback_uncertainty)'''

good = '''    claim_specs = []
    llm_subqueries = []
    det_results = []
    
    for r in relevant_results:
        if _is_venue_capacity_query(r.sub_query) or _is_cancellation_query(r.sub_query):
            det_results.append(r)
        else:
            llm_subqueries.append((r.sub_query, r.chunks))
            
    for sq_ev in llm_subqueries:
        out = await _llm_claims(utterance, [sq_ev], llm, usage)
        if out:
            claim_specs.extend(out[0])
            uncertainty.extend(out[1])

    # Build a lookup from ALL evidence belonging to each sub-query.
    by_id: dict[str, ScoredChunk] = {}
    for _, sub_evidence in sub_query_evidence:
        for scored in sub_evidence:
            by_id[scored.chunk.chunk_id] = scored

    for text, ids in claim_specs:
        valid_ids = [i for i in ids if i in by_id]
        if not valid_ids:
            continue
        cands = [by_id[i] for i in valid_ids]
        drafts.append((text, cands[:3]))

    if det_results:
        fallback_drafts, fallback_uncertainty = heuristic_claims(det_results, engine)
        drafts.extend(fallback_drafts)
        uncertainty.extend(fallback_uncertainty)'''

content = content.replace(bad, good)
with open('aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched hybrid synthesis")
