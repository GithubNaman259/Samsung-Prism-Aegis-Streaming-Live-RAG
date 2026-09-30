import re

with open(r'aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the loop variable name
content = content.replace('for sq, evidence in sub_query_evidence:', 'for sq, loop_evidence in sub_query_evidence:')
content = content.replace('llm_sub_evidence.append((sq, evidence))', 'llm_sub_evidence.append((sq, loop_evidence))')

with open(r'aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Variable shadowing fixed.")
