import re
with open('aegis/aegis/backend/llm.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("timeout=45", "timeout=180")
content = content.replace("timeout=60", "timeout=180")

with open('aegis/aegis/backend/llm.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched LLM Chat Timeout to 180s")
