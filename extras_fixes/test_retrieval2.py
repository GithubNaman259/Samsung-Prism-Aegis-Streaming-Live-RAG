import asyncio
from aegis.backend.retrieval.engine import get_engine
async def main():
    engine = get_engine()
    res = await engine.search("tell me about the domestic travel policy", top_k=3)
    for c in res.chunks:
        print(c.chunk.chunk_id, c.score, c.chunk.text[:50].replace('\n', ' '))
asyncio.run(main())
