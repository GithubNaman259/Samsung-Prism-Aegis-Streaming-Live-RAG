import asyncio
from aegis.backend.retrieval.engine import get_engine, RetrievalResult
from aegis.backend.schemas import SubQuery
from aegis.backend.synthesis import _query_relevant_chunks, MIN_CLAIM_SCORE

async def main():
    engine = get_engine()
    sq2 = SubQuery(text="does the restaurant in Mumbai allow outside catering")
    r2 = await engine.search(sq2.text, top_k=5)
    
    print(f"Number of chunks from search: {len(r2.chunks)}")
    
    relevant = _query_relevant_chunks(r2)
    print(f"Number of relevant chunks: {len(relevant)}")
    
    usable = [s for s in relevant if s.score >= MIN_CLAIM_SCORE]
    print(f"Number of usable chunks: {len(usable)}")
    if not usable:
        print("Usable is empty! That's why it's in uncertainty!")

asyncio.run(main())
