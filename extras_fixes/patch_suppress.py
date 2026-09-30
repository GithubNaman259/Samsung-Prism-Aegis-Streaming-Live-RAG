import re
with open('aegis/aegis/backend/suppression.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad1 = r'''    ("presentation_shorten", re.compile(
        r"\b(shorter|shorten|summari[sz]e|tl;?dr|condense|brief(?:er)?|"
        r"cut it down|trim (?:that|it|this))\b", re.IGNORECASE)),'''
good1 = r'''    ("presentation_shorten", re.compile(
        r"\b(shorter|shorten|summari[sz]e|summary|tl;?dr|condense|brief(?:er)?|"
        r"cut it down|trim (?:that|it|this))\b", re.IGNORECASE)),'''

bad2 = r'''    ("presentation_restructure", re.compile(
        r"\b(bullet(?:s| point.*)?|numbered list|as a list|as a table|"
        r"format (?:that|it|this)|reformat|restructure|rewrite (?:that|it|this))\b",
        re.IGNORECASE)),'''
good2 = r'''    ("presentation_restructure", re.compile(
        r"\b(bullet(?:s| point.*)?|numbered list|as a list|as a table|"
        r"format|reformat|restructure|rewrite)\b",
        re.IGNORECASE)),'''

bad3 = r'''    ("presentation_tone", re.compile(
        r"\b(more formal|less formal|simpler|simplify|plain english|"
        r"more casual|professional tone|explain it like)\b", re.IGNORECASE)),'''
good3 = r'''    ("presentation_tone", re.compile(
        r"\b(formal|simpler|simplify|plain english|"
        r"casual|professional tone|explain it like)\b", re.IGNORECASE)),'''

content = content.replace(bad1, good1).replace(bad2, good2).replace(bad3, good3)
with open('aegis/aegis/backend/suppression.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched suppression.py")
