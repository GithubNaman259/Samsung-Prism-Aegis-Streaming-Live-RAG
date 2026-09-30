import asyncio
from aegis.backend.retrieval.engine import get_engine
from aegis.backend.schemas import SubQuery
from aegis.backend.llm import get_client, Usage
from aegis.backend.synthesis import _llm_claims

async def main():
    engine = get_engine()
    sq1 = SubQuery(text="find a restaurant for an event in Mumbai")
    sq2 = SubQuery(text="tell me about the corporate pet policy")
    
    r1 = await engine.search_many([sq1.text, sq2.text])
    # r1 is list of RetrievalResult
    
    llm = get_client()
    usage = Usage()
    
    sq_ev2 = (r1[1].sub_query, r1[1].chunks)
    
    out2 = await _llm_claims("I need a restaurant for an event in Mumbai and also tell me about the corporate pet policy", [sq_ev2], llm, usage)
    print("PET POLICY OUT:", out2)

asyncio.run(main())
