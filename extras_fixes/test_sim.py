from aegis.backend.synthesis import _best_sentence, cosine_sim, embed_one

doc = "The Mumbai region has three approved venues. Bandra Plaza seats 500 people in a grand theatre layout, ideal for company-wide town halls. Colaba Cafe is a dedicated corporate restaurant in Mumbai that seats 60 people for team dinners. Andheri Boardroom seats 15 people for executive meetings."
query = "actually I need to accommodate 500 people"

cand = _best_sentence(doc, query)
print("BEST SENTENCE:", cand)
sim = cosine_sim(embed_one(query), embed_one(cand))
print("SIMILARITY:", sim)
