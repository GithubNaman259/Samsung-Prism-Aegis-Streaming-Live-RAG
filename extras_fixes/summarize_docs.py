import os
import glob

docs_dir = r'A:\Aegis_Fixed_Clean_Release_v2\aegis\aegis\corpus\docs'
files = sorted(glob.glob(os.path.join(docs_dir, 'Doc_*.md')))

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
        lines = content.split('\n')
        title = next((line.strip() for line in lines if line.startswith('#')), 'No Title')
        
        # Get first paragraph
        paras = [p.strip() for p in content.split('\n\n') if p.strip() and not p.startswith('#')]
        first_para = paras[0][:150] + '...' if paras else 'No content'
        
        print(f"**{os.path.basename(f)}**: {title}")
        print(f"   *Preview:* {first_para}\n")
