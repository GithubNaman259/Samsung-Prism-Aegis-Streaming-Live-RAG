import asyncio
from aegis.backend.retrieval.engine import get_engine
from aegis.backend.synthesis import _llm_claims
from aegis.backend.llm import get_client, Usage

async def main():
    engine = get_engine()
    llm = get_client()
    usage = Usage()
    queries = ["tell me about the domestic travel booking policy", "tell me about the international travel booking policy"]
    results = await engine.search_many(queries, top_k=5)
    
    sq_evidence = [(r.sub_query, r.chunks) for r in results]
    
    print("=== Testing first subquery ===")
    out1 = await _llm_claims("tell me about the international and the domestic travel booking policy", [sq_evidence[0]], llm, usage)
    print("Out1:", out1)
    
    print("\n=== Testing second subquery ===")
    out2 = await _llm_claims("tell me about the international and the domestic travel booking policy", [sq_evidence[1]], llm, usage)
    print("Out2:", out2)

asyncio.run(main())
