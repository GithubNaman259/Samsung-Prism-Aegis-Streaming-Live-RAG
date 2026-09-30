import re

with open(r'aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

# I will find the block that I injected in fix_synthesis2.py and replace it!
# Here is what I injected in fix_synthesis2.py, which was updated by fix_synthesis_var.py:

my_injected_code = '''    import asyncio
    
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

user_original_code = '''    priority_queries = [r.sub_query for r in relevant_results]
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

if my_injected_code in content:
    # Notice that I stripped priority_queries = [r.sub_query for r in relevant_results] in fix_synthesis2.py
    # because my regex caught it!
    # Let me just restore user_original_code
    content = content.replace(my_injected_code, user_original_code)
    print("Reverted synthesize to 5:50pm state!")
else:
    print("Could not find my injected code!")

with open(r'aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)
