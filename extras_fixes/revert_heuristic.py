with open(r'aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_heuristic = '''        if _is_venue_capacity_query(result.sub_query):
            special = _extract_venue_claim(result.sub_query, usable)
            if special is not None:
                text, evidence = special
            else:
                uncertainty.append(result.sub_query)
                continue
        elif _is_cancellation_query(result.sub_query):
            special = _extract_cancellation_claim(result.sub_query, usable)
            if special is not None:
                text, evidence = special
            else:
                uncertainty.append(result.sub_query)
                continue
        else:
            top = usable[0]
            text = _best_sentence(top.chunk.text, result.sub_query)
            evidence = usable[:3]'''

new_heuristic = '''        special = _extract_venue_claim(result.sub_query, usable)
        if special is None and _is_cancellation_query(result.sub_query):
            special = _extract_cancellation_claim(result.sub_query, usable)

        if special is not None:
            text, evidence = special
        elif _is_cancellation_query(result.sub_query):
            # Never answer a cancellation query with an unrelated sentence
            # such as provisional-booking or venue-rate information.
            uncertainty.append(result.sub_query)
            continue
        else:
            top = usable[0]
            text = _best_sentence(top.chunk.text, result.sub_query)
            evidence = usable[:3]'''

if old_heuristic in content:
    content = content.replace(old_heuristic, new_heuristic)
    print("Reverted heuristic_claims")
else:
    print("Could not find heuristic to revert")

with open(r'aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)
