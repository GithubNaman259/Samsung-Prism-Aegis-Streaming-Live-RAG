import re
with open(r'aegis/aegis/frontend/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

pattern = r'if\(added\|\|mod\|\|\(res\.version > 1 && !added && !mod\)\)\{[\s\S]*?p\.appendChild\(t\);\s*\}'
replacement = 'if(added||mod){const t=document.createElement("span");t.className="status-tag";t.textContent=added?"· new":"· patched";p.appendChild(t)}'

js = re.sub(pattern, replacement, js)

with open(r'aegis/aegis/frontend/app.js', 'w', encoding='utf-8') as f:
    f.write(js)
print("JS reverted.")
