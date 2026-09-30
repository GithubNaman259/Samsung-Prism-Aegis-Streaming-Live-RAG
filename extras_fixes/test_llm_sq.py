import asyncio
from aegis.backend.retrieval.engine import get_engine
from aegis.backend.schemas import SubQuery
from aegis.backend.llm import get_client, Usage
from aegis.backend.synthesis import _llm_claims

async def main():
    engine = get_engine()
    sq1 = "find a restaurant for an event in Mumbai"
    
    r1 = await engine.search_many([sq1])
    
    llm = get_client()
    usage = Usage()
    
    sq_ev1 = (r1[0].sub_query, r1[0].chunks)
    
    out1 = await _llm_claims(sq1, [sq_ev1], llm, usage)
    print("RESTAURANT OUT:", out1)

asyncio.run(main())
