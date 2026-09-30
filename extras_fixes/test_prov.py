import asyncio
from aegis.backend.retrieval.engine import get_engine

async def main():
    engine = get_engine()
    results = await engine.search_many(["actually I need to accommodate 500"])
    print("PROVISIONAL CHUNKS:")
    for r in results:
        for c in r.chunks:
            print(" -", c.chunk.chunk_id, c.chunk.text[:60])
            
asyncio.run(main())
