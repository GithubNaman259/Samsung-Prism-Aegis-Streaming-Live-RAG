import os
import glob

history_dir = r'C:\Users\menks\AppData\Roaming\Code\User\History'
print(f'Searching {history_dir}...')

found_files = []
for root, dirs, files in os.walk(history_dir):
    for file in files:
        filepath = os.path.join(root, file)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if 'Aegis can begin speculative retrieval before you finish' in content and 'composer-row' in content:
                    found_files.append((filepath, os.path.getmtime(filepath)))
        except:
            pass

# sort by newest first
found_files.sort(key=lambda x: x[1], reverse=True)
for f in found_files[:10]:
    print(f, os.path.getsize(f[0]))
