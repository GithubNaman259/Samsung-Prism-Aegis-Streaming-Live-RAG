import asyncio
from aegis.backend.retrieval.engine import get_engine

async def main():
    engine = get_engine()
    results = await engine.search_many(["find a venue to accommodate 30 people in Pune"])
    print("CHUNKS:")
    for r in results:
        for c in r.chunks:
            print(" -", c.chunk.chunk_id, c.chunk.text)
            
asyncio.run(main())
