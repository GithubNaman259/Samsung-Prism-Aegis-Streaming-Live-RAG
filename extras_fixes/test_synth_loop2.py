import asyncio
from aegis.backend.retrieval.engine import get_engine
from aegis.backend.synthesis import synthesize
from aegis.backend.schemas import SubQuery
from aegis.backend.llm import get_client

async def main():
    engine = get_engine()
    llm = get_client()
    utterance = "tell me about the international and the domestic travel booking policy"
    # Provide identical subqueries to force duplicates from the LLM!
    sqs = [SubQuery(text="tell me about the international travel booking policy"), 
           SubQuery(text="tell me about the international travel booking policy")]
    
    results = await engine.search_many([s.text for s in sqs], top_k=5)
    
    out = await synthesize("sess123", utterance, sqs, results, engine, None, llm)
    print("Synthesis Output:")
    for c in out.state.claims:
        print(f"Claim: {c.text} | Citations: {c.citations}")

asyncio.run(main())
