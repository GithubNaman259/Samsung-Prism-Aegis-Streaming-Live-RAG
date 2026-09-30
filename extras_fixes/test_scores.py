import asyncio
from aegis.backend.retrieval.engine import get_engine, RetrievalResult
from aegis.backend.schemas import SubQuery
from aegis.backend.synthesis import MIN_RESULT_RELEVANCE_SCORE

async def main():
    engine = get_engine()
    sq2 = SubQuery(text="does the restaurant in Mumbai allow outside catering")
    r2 = await engine.search(sq2.text, top_k=5)
    print(f"MIN SCORE: {MIN_RESULT_RELEVANCE_SCORE}")
    for c in r2.chunks:
        print(f"Score: {c.score:.3f} | {c.chunk.text[:60]}")

asyncio.run(main())
