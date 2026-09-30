import asyncio
from aegis.backend.llm import get_client
from aegis.backend.decomposer import SYSTEM, PROMPT
import json

async def main():
    llm = get_client()
    
    u1 = "tell me about the domestic and the international travel booking policy"
    p1 = PROMPT.format(max_n=2, utterance=u1)
    r1, _ = await llm.complete_json(SYSTEM, p1, max_tokens=300)
    print("Dual Intent RAW:", r1)
    
    u2 = "I need a restaurant for an event in Mumbai and please tell me about the corporate pet policy"
    p2 = PROMPT.format(max_n=2, utterance=u2)
    r2, _ = await llm.complete_json(SYSTEM, p2, max_tokens=300)
    print("Pet Policy RAW:", r2)

asyncio.run(main())
