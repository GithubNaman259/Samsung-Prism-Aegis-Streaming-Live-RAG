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

test("does the restaurant in Mumbai allow outside catering", "However, the Colaba Cafe restaurant in Mumbai allows outside catering subject to a 5000 INR hygiene inspection fee.")
test("find a restaurant for an event in Mumbai", "Colaba Cafe is a dedicated corporate restaurant in Mumbai that seats 60 people for team dinners.")
test("do any of the Mumbai venues provide a DJ and a dance floor", "The Mumbai region has three approved venues.")
