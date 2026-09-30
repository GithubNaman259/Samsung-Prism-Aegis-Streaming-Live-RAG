with open('aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix synthesize threshold
bad1 = "if any(cosine_sim(embed_one(text), embed_one(c.text)) > 0.85 for c in claims):"
good1 = "if any(cosine_sim(embed_one(text), embed_one(c.text)) > 0.70 for c in claims):"
content = content.replace(bad1, good1)

# Fix patch_answer
bad2 = '''        if uncertain:
            if has_new_constraint:
                new_uncertainties.append(new_info)
                changed.append(claim.claim_id)
            else:
                new_claims.append(claim.model_copy(update={"status": "unchanged"}))
            continue
            
        new_claims.append(
            Claim('''

good2 = '''        if uncertain:
            if has_new_constraint:
                new_uncertainties.append(new_info)
                changed.append(claim.claim_id)
            else:
                new_claims.append(claim.model_copy(update={"status": "unchanged"}))
            continue
            
        if any(cosine_sim(embed_one(replacement_text), embed_one(c.text)) > 0.70 for c in new_claims):
            continue
            
        new_claims.append(
            Claim('''

content = content.replace(bad2, good2)
with open('aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched deduplication aggressively")
