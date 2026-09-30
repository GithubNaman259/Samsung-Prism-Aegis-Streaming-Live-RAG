import re
with open('aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the 'remaining' variable assignment
content = content.replace(
    'changed: list[str] = []\n\n    new_claims: list[Claim] = []',
    'changed: list[str] = []\n    new_uncertainties: list[str] = []\n\n    new_claims: list[Claim] = []'
)

content = content.replace(
    'remaining.append(new_info)',
    'new_uncertainties.append(new_info)'
)

content = content.replace(
    'remaining = [\n        u\n        for u in state.uncertainty\n        if cosine_sim(embed_one(u), embed_one(new_info)) < 0.55\n    ]',
    'remaining = [\n        u\n        for u in state.uncertainty\n        if cosine_sim(embed_one(u), embed_one(new_info)) < 0.55\n    ]\n    remaining.extend(new_uncertainties)'
)

with open('aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)
