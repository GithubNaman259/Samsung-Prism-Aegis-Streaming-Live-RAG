import re

# 1. HTML Fix: Remove the inner flex div so all 3 items are direct children of composer-row
with open(r'aegis/aegis/frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove the opening div tag
html = html.replace('<div style="display: flex; gap: 8px; align-items: center;">', '')

# Remove the closing div tag that is immediately after the send button
# The structure is: <button id="send"...>...</button>\n  </div>\n          </div>\n          <div class="composer-meta">
pattern = r'(<button id="send"[^>]*>\s*<span>Send</span>\s*</button>)\s*</div>'
html = re.sub(pattern, r'\1', html, flags=re.DOTALL)

with open(r'aegis/aegis/frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)


# 2. CSS Fix: Neutralize the 	op: 7px; inherited from .icon-button
with open(r'aegis/aegis/frontend/styles.css', 'a', encoding='utf-8') as f:
    f.write('''
/* === FINAL POSITIONING NEUTRALIZER === */
#mic {
    top: auto !important;
    bottom: auto !important;
    left: auto !important;
    right: auto !important;
    margin: 0 !important;
    transform: none !important;
}
''')

print("Perfect alignment applied.")
