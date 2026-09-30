with open('aegis/aegis/backend/decomposer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove contextualize_subqueries from decompose
content = content.replace("raw = contextualize_subqueries(utterance, raw)", "# raw = contextualize_subqueries(utterance, raw)")

with open('aegis/aegis/backend/decomposer.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Disabled contextualize hack")
