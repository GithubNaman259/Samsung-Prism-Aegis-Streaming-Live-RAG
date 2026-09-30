with open('aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'def _is_venue_capacity_query(query: str) -> bool:',
    'def _is_venue_query(query: str) -> bool:\n    q = query.lower()\n    return \"venue\" in q or \"hotel\" in q or \"restaurant\" in q\n\ndef _is_venue_capacity_query(query: str) -> bool:'
)

content = content.replace(
    'if not _is_venue_capacity_query(query):\n        return None',
    'if not _is_venue_query(query):\n        return None'
)

content = content.replace(
    'if not match:\n        return None\n    required = int(match.group(1))',
    'required = int(match.group(1)) if match else 0'
)

content = content.replace(
    '_is_venue_capacity_query(q) or _is_cancellation_query(q)',
    '_is_venue_query(q) or _is_cancellation_query(q)'
)

with open('aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)
