import re
with open('aegis/aegis/backend/config.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("25.0", "180.0")

with open('aegis/aegis/backend/config.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched config.py timeout")
