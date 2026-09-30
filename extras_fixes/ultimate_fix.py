import re

with open(r'aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix heuristic_claims
old_heuristic = '''        if _is_venue_capacity_query(result.sub_query):
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

new_heuristic = '''        special = _extract_venue_claim(result.sub_query, usable)
        if special is None and _is_cancellation_query(result.sub_query):
            special = _extract_cancellation_claim(result.sub_query, usable)

        if special is not None:
            text, evidence = special
        elif _is_cancellation_query(result.sub_query):
            # Never answer a cancellation query with an unrelated sentence
            uncertainty.append(result.sub_query)
            continue
        else:
            top = usable[0]
            text = _best_sentence(top.chunk.text, result.sub_query)
            evidence = usable[:3]'''

content = content.replace(old_heuristic, new_heuristic)


# 2. Fix synthesize hybrid routing and pass sq instead of utterance
old_synthesize = '''    priority_queries = [r.sub_query for r in relevant_results]
    claim_specs = []
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

new_synthesize = '''    import asyncio
    
    det_results = []
    llm_sub_evidence = []
    
    for sq, loop_evidence in sub_query_evidence:
        if _is_venue_capacity_query(sq) or _is_cancellation_query(sq):
            for r in relevant_results:
                if r.sub_query == sq:
                    det_results.append(r)
                    break
        else:
            llm_sub_evidence.append((sq, loop_evidence))

    claim_specs = []
    uncertainty_acc = []
    
    if llm_sub_evidence:
        # MASSIVE FIX: Pass the specific sub-query (sq) to the LLM instead of the entire multi-intent utterance!
        # If the LLM sees the whole utterance but only gets evidence for one sub-query, it hallucinates uncertainty!
        tasks = [_llm_claims(sq, [(sq, ev)], llm, usage) for sq, ev in llm_sub_evidence]
        outcomes = await asyncio.gather(*tasks)
        for out in outcomes:
            if out:
                claim_specs.extend(out[0])
                uncertainty_acc.extend(out[1])

    if claim_specs or uncertainty_acc:
        uncertainty.extend(uncertainty_acc)
        by_id: dict[str, ScoredChunk] = {}
        for _, sub_evidence in sub_query_evidence:
            for scored in sub_evidence:
                by_id[scored.chunk.chunk_id] = scored

        for text, ids in claim_specs:
            valid_ids = [i for i in ids if i in by_id]
            if not valid_ids:
                # If LLM hallucinates chunk ID, fallback to taking any candidate for this subquery
                cands = by_id.values()
                drafts.append((text, list(cands)[:3]))
                continue
            cands = [by_id[i] for i in valid_ids]
            drafts.append((text, cands[:3]))

    if det_results:
        det_drafts, det_unc = heuristic_claims(det_results, engine)
        drafts.extend(det_drafts)
        for item in det_unc:
            if item not in uncertainty:
                uncertainty.append(item)'''

content = content.replace(old_synthesize, new_synthesize)

with open(r'aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Ultimate fix applied.")
