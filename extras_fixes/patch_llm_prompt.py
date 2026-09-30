import re
with open('aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad_str = '''Return JSON:
{{"claims": [{{"text": "one factual sentence", "chunk_ids": ["<chunk id>"]}}],
  "uncertainty": ["any part of the request the evidence does not cover"]}}'''

good_str = '''Return JSON:
{{"claims": [{{"text": "one factual sentence", "chunk_ids": ["Doc_99#c1"]}}],
  "uncertainty": ["any part of the request the evidence does not cover"]}}
(Replace "Doc_99#c1" with the EXACT chunk ID provided in the brackets [ ] above.)'''

content = content.replace(bad_str, good_str)
with open('aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched LLM Prompt")
