# -*- coding: utf-8 -*-
with open(r'aegis/aegis/frontend/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

bad_js = '    if(added||mod){const t=document.createElement("span");t.className="status-tag";t.textContent=added?"· new":"· patched";p.appendChild(t)}'
good_js = '''    if(added||mod||(res.version > 1 && !added && !mod)){
      const t=document.createElement("span");
      t.className = "status-tag " + (added ? "new-tag" : (mod ? "patched-tag" : "reused-tag"));
      t.textContent = added ? "\u00B7 NEW" : (mod ? "\u00B7 PATCHED" : "\u00B7 REUSED");
      p.appendChild(t);
    }'''

js = js.replace(bad_js, good_js)
with open(r'aegis/aegis/frontend/app.js', 'w', encoding='utf-8') as f:
    f.write(js)
print("Patched app.js tags")
