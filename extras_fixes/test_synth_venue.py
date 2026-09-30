import asyncio
from aegis.backend.retrieval.engine import get_engine
from aegis.backend.synthesis import _llm_claims
from aegis.backend.llm import get_client, Usage

async def main():
    engine = get_engine()
    llm = get_client()
    res = await engine.search("find a restaurant for an event in Mumbai", top_k=5)
    sq_ev = (res.sub_query, res.chunks)
    out = await _llm_claims("find a restaurant for an event in Mumbai and please tell me about the corporate pet policy", [sq_ev], llm, Usage())
    print("Claims:", out[0] if out else "None")
asyncio.run(main())
