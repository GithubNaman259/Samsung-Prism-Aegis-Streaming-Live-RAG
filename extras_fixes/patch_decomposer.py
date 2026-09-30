with open('aegis/aegis/backend/decomposer.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("but |", "")

with open('aegis/aegis/backend/decomposer.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Removed 'but ' from REFINE_MARKERS")
