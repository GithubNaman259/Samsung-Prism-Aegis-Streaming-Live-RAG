import re

with open(r'aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(
    r'    priority_queries = \[r\.sub_query for r in relevant_results\].*?    else:\n        drafts, uncertainty = heuristic_claims\(relevant_results, engine\)',
    re.DOTALL
)

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

if pattern.search(content):
    content = pattern.sub(new_synthesize, content)
    print("Fixed hybrid routing in synthesize.")
else:
    print("Could not find synthesize pattern.")

with open(r'aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)
