import re

with open(r'aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad = '''    if det_results:
        det_drafts, det_unc = heuristic_claims(det_results, engine)
        drafts.extend(det_drafts)
        for item in det_unc:
            if item not in uncertainty:
                uncertainty.append(item)

    claims: list[Claim] = []
    for idx, (text, candidates) in enumerate(drafts, start=1):
        # Trust gauntlet: filter irrelevant-but-grounded claims
        vec_text = embed_one(text)
        is_responsive = False'''

good = '''    det_drafts_set = set()
    if det_results:
        det_drafts, det_unc = heuristic_claims(det_results, engine)
        drafts.extend(det_drafts)
        det_drafts_set = {t for t, _ in det_drafts}
        for item in det_unc:
            if item not in uncertainty:
                uncertainty.append(item)

    claims: list[Claim] = []
    for idx, (text, candidates) in enumerate(drafts, start=1):
        if text in det_drafts_set:
            # Deterministic claims are mathematically generated and proven.
            # Bypass the fuzzy LLM hallucination gauntlet entirely.
            chunk_ids, citations, confidence, uncertain = verify_claim(text, candidates, engine)
            if not uncertain:
                claims.append(Claim(claim_id=f"c{idx}", text=text, citations=citations, chunk_ids=chunk_ids, status="added", confidence=confidence, is_uncertain=False))
            else:
                uncertainty.append(text)
            continue

        # Trust gauntlet: filter irrelevant-but-grounded claims
        vec_text = embed_one(text)
        is_responsive = False'''

if bad in content:
    content = content.replace(bad, good)
    print("Patched gauntlet")
else:
    print("Could not find bad block")

with open(r'aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)
