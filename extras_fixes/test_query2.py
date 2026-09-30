import asyncio
from aegis.backend.pipeline import AegisPipeline

async def main():
    pipe = AegisPipeline()
    async for chunk in pipe.process("test_sess", "find a venue to accommodate 30 people in Pune and also retrieve the cancellation policy for the venue", "test_user"):
        print(chunk)

asyncio.run(main())
