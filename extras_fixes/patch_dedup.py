import re
with open('aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad_str = '''        if uncertain:
            uncertainty.append(text)
            continue

        claims.append(
            Claim(
                claim_id=f"c{idx}","""

good_str = '''        if uncertain:
            uncertainty.append(text)
            continue

        # Deduplicate claims to prevent redundant LLM outputs
        if any(cosine_sim(embed_one(text), embed_one(c.text)) > 0.85 for c in claims):
            continue

        claims.append(
            Claim(
                claim_id=f"c{idx}","""

content = content.replace(bad_str, good_str)
with open('aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched deduplication")
