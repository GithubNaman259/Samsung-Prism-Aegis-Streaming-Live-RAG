import asyncio
from aegis.backend.retrieval.engine import get_engine
from aegis.backend.synthesis import _llm_claims
from aegis.backend.llm import get_client, Usage

async def main():
    engine = get_engine()
    llm = get_client()
    usage = Usage()
    res = await engine.search("tell me about the international travel booking policy", top_k=5)
    sq_ev = (res.sub_query, res.chunks)
    out = await _llm_claims("tell me about the domestic and the international travel booking policy", [sq_ev], llm, usage)
    print("Claims:", out[0] if out else "None")
asyncio.run(main())
