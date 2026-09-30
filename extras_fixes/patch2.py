import re
with open('aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_logic = '''        is_responsive = False
        for sq in sub_queries:
            if cosine_sim(vec_text, embed_one(sq.text)) > 0.15 or len(set(tokenize(text)) & set(tokenize(sq.text))) > 1:
                is_responsive = True
                break
                
        if not is_responsive:
            # Drop grounded but irrelevant claim
            continue'''

new_logic = '''        is_responsive = False
        text_lower = text.lower()
        for sq in sub_queries:
            sq_lower = sq.text.lower()
            if cosine_sim(vec_text, embed_one(sq.text)) >= 0.12 or len(set(tokenize(text)) & set(tokenize(sq.text))) >= 1:
                # If it's a venue search but it returns rate comparisons, filter it out
                if "rate" in text_lower or "percent higher" in text_lower or "provisional booking" in text_lower:
                    if "rate" not in sq_lower and "cost" not in sq_lower and "price" not in sq_lower and "provisional" not in sq_lower:
                        continue
                is_responsive = True
                break
                
        if not is_responsive:
            # Drop grounded but irrelevant claim
            continue'''

content = content.replace(old_logic, new_logic)

with open('aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)
