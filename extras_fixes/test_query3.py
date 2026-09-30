import asyncio
from aegis.backend.pipeline import AegisPipeline

async def main():
    pipe = AegisPipeline()
    res = await pipe.run_turn("test_sess", "find a venue to accommodate 30 people in Pune and also retrieve the cancellation policy for the venue")
    for claim in res.answer.claims:
        print("CLAIM:", claim.text, claim.status)
    print("UNCERTAINTY:", res.answer.uncertainty)

asyncio.run(main())
