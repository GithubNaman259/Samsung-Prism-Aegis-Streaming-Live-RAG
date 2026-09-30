# -*- coding: utf-8 -*-
import asyncio
from aegis.backend.synthesis import patch_answer, find_affected_claims, Claim
from aegis.backend.retrieval.engine import get_engine, RetrievalResult, ScoredChunk
from aegis.backend.schemas import AnswerState, SubQuery
import aegis.backend.config as config

async def main():
    engine = get_engine()
    # Mock AnswerState v1
    c1 = Claim(claim_id="c1", text="Colaba Cafe is a dedicated corporate restaurant in Mumbai that seats 60 people for team dinners.", citations=["Doc_19 §1"], chunk_ids=["Doc_19#c1"], status="added", confidence=0.9, is_uncertain=False)
    c2 = Claim(claim_id="c2", text="The Colaba Cafe restaurant in Mumbai allows outside catering subject to a 5000 INR hygiene inspection fee.", citations=["Doc_19 §2"], chunk_ids=["Doc_19#c2"], status="added", confidence=0.9, is_uncertain=False)
    c3 = Claim(claim_id="c3", text="Certified service animals are the only exception to the pet policy.", citations=["Doc_20 §2"], chunk_ids=["Doc_20#c2"], status="added", confidence=0.9, is_uncertain=False)
    
    state = AnswerState(session_id="s1", claims=[c1, c2, c3], uncertainty=[], answer_version=1, last_utterance="I need a restaurant for an event in Mumbai and also tell me about the corporate pet policy", turn_history=[])
    
    affected = find_affected_claims("actually I need to accommodate 500 people", state.claims)
    print("AFFECTED CLAIMS:", [c.claim_id for c in affected])
    
    sq = SubQuery(text="actually I need to accommodate 500 people")
    results = await engine.search_many([sq.text])
    
    print("RETRIEVED CHUNKS:")
    for r in results:
        for c in r.chunks:
            print(" -", c.chunk.chunk_id, c.chunk.text[:50])
            
    out = await patch_answer("s1", "actually I need to accommodate 500 people", state, [sq], results, engine)
    print("\nPATCHED CLAIMS:")
    for c in out.state.claims:
        print(c.status, ":", c.text)
        
    print("\nUNCERTAINTY:")
    print(out.state.uncertainty)

asyncio.run(main())
