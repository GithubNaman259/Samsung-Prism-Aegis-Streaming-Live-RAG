with open('aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad_str = '''def _is_venue_capacity_query(query: str) -> bool:
    q = query.lower()
    return "venue" in q and any(
        marker in q
        for marker in ("accommodate", "capacity", "people", "headcount", "seat")
    )
    q = query.lower()
    return "venue" in q and any(
        marker in q
        for marker in ("accommodate", "capacity", "people", "headcount", "seat")
    )'''

good_str = '''def _is_venue_capacity_query(query: str) -> bool:
    q = query.lower()
    return "venue" in q and any(
        marker in q
        for marker in ("accommodate", "capacity", "people", "headcount", "seat")
    )'''

content = content.replace(bad_str, good_str)

with open('aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)
