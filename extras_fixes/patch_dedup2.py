with open('aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad = '''        if uncertain:
            uncertainty.append(text)
            continue

        claims.append(
            Claim('''

good = '''        if uncertain:
            uncertainty.append(text)
            continue

        if any(cosine_sim(embed_one(text), embed_one(c.text)) > 0.85 for c in claims):
            continue

        claims.append(
            Claim('''

content = content.replace(bad, good)
with open('aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched deduplication")
