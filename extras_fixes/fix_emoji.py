# -*- coding: utf-8 -*-
with open(r'aegis/aegis/frontend/index.html', 'r', encoding='utf-8') as f:
    html = f.read()
html = html.replace('<span class="mic-emoji">??</span>', '<span class="mic-emoji">\U0001f3a4</span>')
with open(r'aegis/aegis/frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
