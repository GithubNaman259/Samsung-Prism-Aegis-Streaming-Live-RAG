import os
import time

history_dir = r'C:\Users\menks\AppData\Roaming\Code\User\History'
found_files = []
for root, dirs, files in os.walk(history_dir):
    for file in files:
        filepath = os.path.join(root, file)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if 'def synthesize' in content and 'RetrievalEngine' in content:
                    found_files.append((filepath, os.path.getmtime(filepath)))
        except:
            pass

found_files.sort(key=lambda x: x[1], reverse=True)
for f in found_files[:15]:
    print(f[0], os.path.getsize(f[0]), time.ctime(f[1]))
