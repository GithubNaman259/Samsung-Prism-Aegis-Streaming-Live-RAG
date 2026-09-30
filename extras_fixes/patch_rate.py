import re
with open('aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad_str = '''if "rate" in text_lower or "percent higher" in text_lower or "provisional booking" in text_lower:
                    if "rate" not in sq_lower and "cost" not in sq_lower and "price" not in sq_lower and "provisional" not in sq_lower:
                        continue'''

good_str = '''if re.search(r'\\brates?\\b', text_lower) or "percent higher" in text_lower or "provisional booking" in text_lower:
                    if not re.search(r'\\brates?\\b', sq_lower) and "cost" not in sq_lower and "price" not in sq_lower and "provisional" not in sq_lower:
                        continue'''

content = content.replace(bad_str, good_str)
with open('aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched rate filter")
