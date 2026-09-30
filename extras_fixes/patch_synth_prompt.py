with open('aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad = '''Rules:
- A claim must be supported by evidence belonging to the same sub-query.
- NEVER use evidence from one sub-query to answer another sub-query.
- Every claim must directly answer the specific sub-query, not merely mention
  a related topic.
- For constraint-based requests, every explicit constraint in the sub-query
  must be satisfied by the claim or its evidence.
- Do not list alternatives that fail an explicit numeric or factual constraint.
- For example, if the request requires capacity 30, do not return a venue
  whose evidence says it seats only 25.
- If no evidence satisfies the constraints, return that part in "uncertainty".'''

good = '''Rules:
- A claim must be supported by evidence belonging to the same sub-query.
- Every claim must directly answer the specific sub-query, not merely mention a related topic.
- If the evidence does not EXPLICITLY answer the subquery, do NOT create a claim. Put the subquery in "uncertainty".
- Do not combine evidence from completely different topics.
- For constraint-based requests, every explicit constraint in the sub-query must be satisfied by the claim or its evidence.
- If no evidence satisfies the constraints, return that part in "uncertainty".'''

content = content.replace(bad, good)
with open('aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched synthesis prompt")
