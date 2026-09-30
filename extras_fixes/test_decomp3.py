import asyncio
from aegis.backend.decomposer import decompose
from aegis.backend.llm import get_client

async def main():
    llm = get_client()
    print("Is Stub?", llm.is_stub)
    utterance = "tell me about the domestic and the international travel booking policy"
    sqs, usage = await decompose(utterance, client=llm, max_n=2)
    print("Dual Intent:", [s.text for s in sqs])
asyncio.run(main())
