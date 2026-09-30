import asyncio
from aegis.backend.retrieval.engine import get_engine
from aegis.backend.schemas import SubQuery

async def main():
    engine = get_engine()
    res = await engine.search("tell me about the corporate pet policy")
    for r in res.chunks:
        print(r.chunk.chunk_id, r.chunk.text[:50])
asyncio.run(main())
