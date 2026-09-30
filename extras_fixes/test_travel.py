import asyncio
from aegis.backend.retrieval.engine import get_engine

async def main():
    engine = get_engine()
    queries = ["tell me about the domestic travel booking policy", "tell me about the international travel booking policy"]
    results = await engine.search_many(queries, top_k=5)
    for r in results:
        print(f"\nSub-query: {r.sub_query}")
        for i, chunk in enumerate(r.chunks):
            print(f"Chunk {i+1} [{chunk.chunk.chunk_id}] Score {chunk.score:.3f}: {chunk.chunk.text[:100]}...")

asyncio.run(main())
