import asyncio
from aegis.backend.retrieval.engine import get_engine
from aegis.backend.synthesis import verify_claim

async def main():
    engine = get_engine()
    queries = ["tell me about the international travel booking policy", "retrieve the international travel booking policy details"]
    results = await engine.search_many(queries, top_k=5)
    
    # Emulate the candidates list from valid_ids
    by_id = {}
    for r in results:
        for c in r.chunks:
            by_id[c.chunk.chunk_id] = c
            
    candidates = [by_id["Doc_10#c1"]]
    text = "International travel is booked through the corporate travel desk with a minimum of 21 days notice. Bookings inside 21 days require senior director approval, which is a stricter bar than the domestic 14 day rule."
    
    chunk_ids, citations, confidence, uncertain = verify_claim(text, candidates, engine)
    print(f"chunk_ids: {chunk_ids}")
    print(f"citations: {citations}")
    print(f"confidence: {confidence}")
    print(f"uncertain: {uncertain}")

asyncio.run(main())
