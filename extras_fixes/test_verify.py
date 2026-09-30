import asyncio
from aegis.backend.retrieval.engine import get_engine
from aegis.backend.synthesis import verify_claim

async def main():
    engine = get_engine()
    res = await engine.search("find a restaurant for an event in Mumbai", top_k=1)
    text = "Colaba Cafe is a dedicated corporate restaurant in Mumbai that seats 60 people for team dinners."
    chunk_ids, citations, confidence, uncertain = verify_claim(text, res.chunks, engine)
    print("Uncertain:", uncertain)
    print("Confidence:", confidence)

asyncio.run(main())
