import re
with open(r'aegis/aegis/frontend/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

pattern = r'if\(added\|\|mod\)\{const t=document\.createElement\("span"\);t\.className="status-tag";t\.textContent=added\?[^\}]+p\.appendChild\(t\)\}'
replacement = '''if(added||mod||(res.version > 1 && !added && !mod)){
      const t=document.createElement("span");
      t.className = "status-tag " + (added ? "new-tag" : (mod ? "patched-tag" : "reused-tag"));
      t.textContent = added ? "NEW" : (mod ? "PATCHED" : "REUSED");
      p.appendChild(t);
    }'''

js = re.sub(pattern, replacement, js)

with open(r'aegis/aegis/frontend/app.js', 'w', encoding='utf-8') as f:
    f.write(js)
print("Patched app.js")
