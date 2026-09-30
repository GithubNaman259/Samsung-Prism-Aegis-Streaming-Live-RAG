import asyncio
from aegis.backend.decomposer import decompose
async def main():
    utterance = "tell me about the domestic and the international travel booking policy"
    sqs, usage = await decompose(utterance, max_n=2)
    print("Dual Intent:", [s.text for s in sqs])
    
    utterance2 = "I need a restaurant for an event in Mumbai and please tell me about the corporate pet policy"
    sqs2, usage2 = await decompose(utterance2, max_n=2)
    print("Pet Policy:", [s.text for s in sqs2])
asyncio.run(main())
