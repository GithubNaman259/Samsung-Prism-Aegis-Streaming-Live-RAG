import re
from aegis.backend.synthesis import embed_one, cosine_sim, tokenize

text = 'Orchid Hall seats 30 people in boardroom layout and 45 in theatre layout, making it the default choice for mid-size offsites. Sahyadri Conference Centre seats 120 in theatre layout and 60 in banquet rounds.'
sq_text = 'find a venue to accommodate 30 people in Pune'

vec_text = embed_one(text)
is_responsive = False
text_lower = text.lower()
sq_lower = sq_text.lower()
sq_terms = set(tokenize(sq_text))

stop = {"a","an","the","and","or","of","for","to","in","on","at","is","are","do","does","i","we","you","it","that","this","what","how","want","need","know","me","my","get","tell","give","with","about","whats"}
sq_content = sq_terms - stop
text_content = set(tokenize(text)) - stop

if len(sq_content) > 0:
    overlap_ratio = len(text_content & sq_content) / len(sq_content)
else:
    overlap_ratio = 0.0
    
sim = cosine_sim(vec_text, embed_one(sq_text))
print("Overlap Ratio:", overlap_ratio)
print("Cosine Sim:", sim)

if sim >= 0.35 or overlap_ratio >= 0.40:
    print("Base threshold passed!")
    if re.search(r'\brates?\b', text_lower) or "percent higher" in text_lower or "provisional booking" in text_lower:
        if not re.search(r'\brates?\b', sq_lower) and "cost" not in sq_lower and "price" not in sq_lower and "provisional" not in sq_lower:
            print("Filtered by rate guard!")
        else:
            print("Passed rate guard!")
            is_responsive = True
    else:
        is_responsive = True
        
print("Is Responsive:", is_responsive)
