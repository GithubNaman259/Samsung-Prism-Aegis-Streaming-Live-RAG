import re
with open('aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad_str = '''            if cosine_sim(vec_text, embed_one(sq.text)) >= 0.25 or overlap_ratio >= 0.40:'''
good_str = '''            
            # Use content words only for the overlap ratio to avoid stop-word inflation
            stop = {"a","an","the","and","or","of","for","to","in","on","at","is","are","do","does","i","we","you","it","that","this","what","how","want","need","know","me","my","get","tell","give","with","about","whats"}
            sq_content = sq_terms - stop
            text_content = set(tokenize(text)) - stop
            
            if len(sq_content) > 0:
                overlap_ratio = len(text_content & sq_content) / len(sq_content)
            else:
                overlap_ratio = 0.0
                
            if cosine_sim(vec_text, embed_one(sq.text)) >= 0.35 or overlap_ratio >= 0.40:'''

content = content.replace(bad_str, good_str)
with open('aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched Trust Gauntlet again")
