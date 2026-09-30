import asyncio
from aegis.backend.retrieval.engine import get_engine
from aegis.backend.schemas import SubQuery
from aegis.backend.synthesis import verify_claim

async def main():
    engine = get_engine()
    sq = SubQuery(text="actually the event blew up make sure it can accommodate 500 people")
    r = await engine.search(sq.text, top_k=5)
    evidence = engine.fuse_results([r], top_k=5)
    
    text = "Bandra Plaza seats 500 people in a grand theatre layout, ideal for company-wide town halls."
    chunk_ids, citations, conf, unc = verify_claim(text, evidence, engine)
    print(f"verify_claim: unc={unc}, citations={citations}, chunk_ids={chunk_ids}")

asyncio.run(main())
