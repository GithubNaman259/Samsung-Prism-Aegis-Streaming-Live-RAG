from aegis.backend.embeddings import embed_one, cosine_sim
s1 = 'Domestic travel must be booked through the corporate travel desk and requires at least 14 days advance notice.'
s2 = 'International travel is booked through the corporate travel desk with a minimum of 21 days notice.'
print(cosine_sim(embed_one(s1), embed_one(s2)))
