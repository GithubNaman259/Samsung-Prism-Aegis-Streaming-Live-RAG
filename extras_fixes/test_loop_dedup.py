from aegis.backend.embeddings import embed_one, cosine_sim
from aegis.backend.schemas import Claim

claims = []
text = "International travel is booked through the corporate travel desk with a minimum of 21 days notice."

# First iteration
claims.append(Claim(claim_id="c1", text=text, citations=[], chunk_ids=[], status="added", confidence=1.0, is_uncertain=False))

# Second iteration
if any(cosine_sim(embed_one(text), embed_one(c.text)) > 0.85 for c in claims):
    print("Dedup worked!")
else:
    print("Dedup failed!")
