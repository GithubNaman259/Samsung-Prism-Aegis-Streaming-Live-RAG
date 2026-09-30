import glob
import os

docs = sorted(glob.glob(r'A:\Aegis_Fixed_Clean_Release_v2\aegis\aegis\corpus\docs\Doc_*.md'))
for doc in docs:
    with open(doc, 'r', encoding='utf-8') as f:
        title = "No Title"
        for line in f:
            if line.startswith('#'):
                title = line.strip()
                break
        print(f"{os.path.basename(doc)}: {title}")
