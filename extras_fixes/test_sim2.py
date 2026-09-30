from aegis.backend.synthesis import cosine_sim, embed_one

t1 = "Bandra Plaza seats 500 people in a grand theatre layout, ideal for company-wide town halls."
t2 = "The Colaba Cafe restaurant in Mumbai allows outside catering subject to a 5000 INR hygiene inspection fee."
t3 = "Certified service animals are the only exception to the pet policy."

print("Sim with catering:", cosine_sim(embed_one(t1), embed_one(t2)))
print("Sim with pet policy:", cosine_sim(embed_one(t1), embed_one(t3)))
