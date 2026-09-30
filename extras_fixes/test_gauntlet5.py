from aegis.backend.embeddings import tokenize, embed_one, cosine_sim

def test(sq_text, text):
    stop = {"a","an","the","and","or","of","for","to","in","on","at","is","are","do","does","i","we","you","it","that","this","what","how","want","need","know","me","my","get","tell","give","with","about","whats"}
    sq_terms = set(tokenize(sq_text))
    sq_content = sq_terms - stop
    text_content = set(tokenize(text)) - stop
    
    if len(sq_content) > 0:
        overlap_ratio = len(text_content & sq_content) / len(sq_content)
    else:
        overlap_ratio = 0.0
        
    sim = cosine_sim(embed_one(text), embed_one(sq_text))
    passed = sim >= 0.35 or overlap_ratio >= 0.40
    print(f"SQ: {sq_text}")
    print(f"Text: {text}")
    print(f"Overlap: {overlap_ratio:.2f}, Sim: {sim:.2f} -> PASS: {passed}\n")

c1 = "All domestic travel is booked through the corporate travel desk."
sq1 = "tell me about the domestic travel policy"
test(sq1, c1)

c3 = "International travel is booked through the corporate travel desk with a minimum of 21 days notice."
sq2 = "tell me about the international travel policy"
test(sq2, c3)
