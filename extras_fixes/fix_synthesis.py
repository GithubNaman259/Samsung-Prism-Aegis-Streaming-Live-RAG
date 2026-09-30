import re

with open(r'aegis/aegis/frontend/index.html', 'r', encoding='utf-8') as f:
    pass # just a dummy to ensure paths

with open(r'aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix heuristic_claims
old_heuristic = '''        special = _extract_venue_claim(result.sub_query, usable)
        if special is None and _is_cancellation_query(result.sub_query):
            special = _extract_cancellation_claim(result.sub_query, usable)

        if special is not None:
            text, evidence = special
        elif _is_cancellation_query(result.sub_query):
            # Never answer a cancellation query with an unrelated sentence
            # such as provisional-booking or venue-rate information.
            uncertainty.append(result.sub_query)
            continue
        else:
            top = usable[0]
            text = _best_sentence(top.chunk.text, result.sub_query)
            evidence = usable[:3]'''

new_heuristic = '''        if _is_venue_capacity_query(result.sub_query):
            special = _extract_venue_claim(result.sub_query, usable)
            if special is not None:
                text, evidence = special
            else:
                uncertainty.append(result.sub_query)
                continue
        elif _is_cancellation_query(result.sub_query):
            special = _extract_cancellation_claim(result.sub_query, usable)
            if special is not None:
                text, evidence = special
            else:
                uncertainty.append(result.sub_query)
                continue
        else:
            top = usable[0]
            text = _best_sentence(top.chunk.text, result.sub_query)
            evidence = usable[:3]'''

if old_heuristic in content:
    content = content.replace(old_heuristic, new_heuristic)
    print("Fixed heuristic_claims.")
else:
    print("Could not find old_heuristic.")

# 2. Fix synthesize hybrid routing
old_synthesize = '''    priority_queries = [r.sub_query for r in relevant_results]
    needs_deterministic_grounding = any(
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

            # Preserve uncertainty already produced by the LLM.
            for item in fallback_uncertainty:
                if item not in uncertainty:
                    uncertainty.append(item)

    else:
        drafts, uncertainty = heuristic_claims(relevant_results, engine)'''

new_synthesize = '''    import asyncio
    
    det_results = []
    llm_sub_evidence = []
    
    for sq, evidence in sub_query_evidence:
        if _is_venue_capacity_query(sq) or _is_cancellation_query(sq):
            for r in relevant_results:
                if r.sub_query == sq:
                    det_results.append(r)
                    break
        else:
            llm_sub_evidence.append((sq, evidence))

    claim_specs = []
    uncertainty_acc = []
    
    if llm_sub_evidence:
        tasks = [_llm_claims(utterance, [sq_ev], llm, usage) for sq_ev in llm_sub_evidence]
        outcomes = await asyncio.gather(*tasks)
        for out in outcomes:
            if out:
                claim_specs.extend(out[0])
                uncertainty_acc.extend(out[1])

    # Add LLM claims to drafts
    if claim_specs or uncertainty_acc:
        uncertainty.extend(uncertainty_acc)
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

    # Add deterministic claims to drafts
    if det_results:
        det_drafts, det_unc = heuristic_claims(det_results, engine)
        drafts.extend(det_drafts)
        for item in det_unc:
            if item not in uncertainty:
                uncertainty.append(item)'''

if old_synthesize in content:
    content = content.replace(old_synthesize, new_synthesize)
    print("Fixed hybrid routing in synthesize.")
else:
    print("Could not find old_synthesize.")

with open(r'aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)
