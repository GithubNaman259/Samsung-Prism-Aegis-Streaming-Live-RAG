import re

with open(r'aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix find_affected_claims
old_find = '''def find_affected_claims(
    new_info: str, claims: Sequence[Claim], top_n: int = 2
) -> list[Claim]:
    """Identify affected claims using semantic similarity and numeric constraints."""
    if not claims:
        return []
        
    new_lower = new_info.lower()
    new_numbers = set(re.findall(r"\d+", new_lower))
    
    scored_claims = []
    vec = embed_one(new_info)
    
    for c in claims:
        text_lower = c.text.lower()
        claim_numbers = set(re.findall(r"\d+", text_lower))
        
        sim = cosine_sim(vec, embed_one(c.text))
        score = sim
        
        # Boost score if new info implies a capacity update and the claim discusses capacity
        if new_numbers and ("people" in new_lower or "capacity" in new_lower):
            if "people" in text_lower or "capacity" in text_lower or "seats" in text_lower:
                score += 0.5
                
        scored_claims.append((score, c))
        
    scored = sorted(scored_claims, key=lambda pair: -pair[0])
    affected = [c for score, c in scored if score >= 0.18][:top_n]
    return affected or [scored[0][1]]'''

new_find = '''def find_affected_claims(
    new_info: str, claims: Sequence[Claim], top_n: int = 1
) -> list[Claim]:
    """Identify affected claims using semantic similarity and numeric constraints."""
    if not claims:
        return []
        
    new_lower = new_info.lower()
    new_numbers = set(re.findall(r"\d+", new_lower))
    
    scored_claims = []
    vec = embed_one(new_info)
    
    for c in claims:
        text_lower = c.text.lower()
        score = cosine_sim(vec, embed_one(c.text))
        
        if new_numbers and ("people" in new_lower or "capacity" in new_lower or "seats" in new_lower):
            if "people" in text_lower or "capacity" in text_lower or "seats" in text_lower:
                score += 0.5
                
        scored_claims.append((score, c))
        
    scored = sorted(scored_claims, key=lambda pair: -pair[0])
    affected = [c for score, c in scored if score >= 0.18][:top_n]
    return affected or [scored[0][1]]'''

if old_find in content:
    content = content.replace(old_find, new_find)
    print("Replaced find_affected_claims")
else:
    print("Failed to replace find_affected_claims")

# Fix patch_answer
old_patch_logic = '''        found_satisfying_evidence = False
        if evidence:
            for ev in evidence:
                candidate = _best_sentence(ev.chunk.text, new_info)
                if has_new_constraint:
                    cand_nums = [int(n) for n in re.findall(r"\d+", candidate)]
                    if any(n >= req_num for n in cand_nums):
                        replacement_text = candidate
                        found_satisfying_evidence = True
                        break
                else:
                    replacement_text = candidate
                    found_satisfying_evidence = True
                    break'''

new_patch_logic = '''        found_satisfying_evidence = False
        if evidence:
            new_lower = new_info.lower()
            vec_new = embed_one(new_info)
            ranked_ev = sorted(evidence, key=lambda e: -cosine_sim(vec_new, embed_one(e.chunk.text)))
            for ev in ranked_ev:
                candidate = _best_sentence(ev.chunk.text, new_info)
                cand_sim = cosine_sim(vec_new, embed_one(candidate))
                
                if has_new_constraint:
                    cand_nums = [int(n) for n in re.findall(r"\d+", candidate)]
                    if any(n >= req_num for n in cand_nums):
                        # Ensure semantic relevance and context match
                        if cand_sim < 0.25:
                            continue
                        if ("people" in new_lower or "capacity" in new_lower or "seats" in new_lower):
                            if not ("people" in candidate.lower() or "seats" in candidate.lower() or "capacity" in candidate.lower()):
                                continue
                        replacement_text = candidate
                        found_satisfying_evidence = True
                        break
                else:
                    if cand_sim < 0.25:
                        continue
                    replacement_text = candidate
                    found_satisfying_evidence = True
                    break'''

if old_patch_logic in content:
    content = content.replace(old_patch_logic, new_patch_logic)
    print("Replaced patch_answer logic")
else:
    print("Failed to replace patch_answer logic")

with open(r'aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)
