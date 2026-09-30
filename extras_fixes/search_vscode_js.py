# -*- coding: utf-8 -*-
import os

history_dir = r'C:\Users\menks\AppData\Roaming\Code\User\History'
found_files = []
for root, dirs, files in os.walk(history_dir):
    for file in files:
        filepath = os.path.join(root, file)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if 'status-tag' in content and 'p.appendChild(t)' in content and 'function escapeHtml(s)' in content:
                    found_files.append((filepath, os.path.getmtime(filepath)))
        except:
            pass

found_files.sort(key=lambda x: x[1], reverse=True)
for f in found_files[:10]:
    print(f, os.path.getsize(f[0]))
