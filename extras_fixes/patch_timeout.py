import re
with open('aegis/aegis/backend/llm.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("timeout=0.35", "timeout=5.0")

with open('aegis/aegis/backend/llm.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched LLM Timeout")
