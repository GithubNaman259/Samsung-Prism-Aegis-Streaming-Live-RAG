import asyncio
from aegis.backend.retrieval.engine import get_engine, RetrievalResult
from aegis.backend.schemas import SubQuery
from aegis.backend.synthesis import _query_relevant_chunks, MIN_CLAIM_SCORE, _best_sentence
import re

async def main():
    engine = get_engine()
    sq = SubQuery(text="actually the event blew up make sure it can accommodate 500 people")
    r = await engine.search(sq.text, top_k=5)
    
    print(f"Number of chunks from search: {len(r.chunks)}")
    
    relevant = _query_relevant_chunks(r)
    print(f"Number of relevant chunks: {len(relevant)}")
    
    usable = [s for s in relevant if s.score >= MIN_CLAIM_SCORE]
    print(f"Number of usable chunks: {len(usable)}")
    
    evidence = engine.fuse_results([r], top_k=5)
    print(f"Number of fused evidence: {len(evidence)}")
    
    req_num = 500
    for ev in evidence:
        candidate = _best_sentence(ev.chunk.text, sq.text)
        cand_nums = [int(n) for n in re.findall(r'\d+', candidate)]
        valid = any(n >= req_num for n in cand_nums)
        print(f"Candidate: {candidate} | Valid: {valid}")

asyncio.run(main())
