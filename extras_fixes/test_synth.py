import asyncio
from aegis.backend.synthesis import synthesize, _is_venue_capacity_query
from aegis.backend.retrieval.engine import get_engine, RetrievalResult
from aegis.backend.schemas import AnswerState, SubQuery

async def main():
    engine = get_engine()
    sq1 = SubQuery(text="find a restaurant for an event in Mumbai")
    sq2 = SubQuery(text="does the restaurant in Mumbai allow outside catering")
    
    # Do retrieval
    r1 = await engine.search(sq1.text, top_k=5)
    r2 = await engine.search(sq2.text, top_k=5)
    
    print(f"R1 chunks: {len(r1.chunks)}")
    if r1.chunks: print(f"R1 top chunk: {r1.chunks[0].chunk.text}")
    print(f"R2 chunks: {len(r2.chunks)}")
    if r2.chunks: print(f"R2 top chunk: {r2.chunks[0].chunk.text}")
    
    print(f"needs deterministic? {any(_is_venue_capacity_query(q.text) for q in [sq1, sq2])}")
    
    from aegis.backend.synthesis import heuristic_claims
    drafts, unc = heuristic_claims([r1, r2], engine)
    print(f"Heuristic drafts: {drafts}")
    print(f"Heuristic unc: {unc}")

asyncio.run(main())
