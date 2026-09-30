import asyncio
from aegis.backend.pipeline import AegisPipeline

async def main():
    pipe = AegisPipeline()
    class DummyBus:
        async def publish(self, topic, payload): pass
        def reset_clock(self): pass
        def set_session(self, s): pass
    res = await pipe.run_turn("test", "I need a restaurant for an event in Mumbai and also tell me about the corporate pet policy", DummyBus())
    for c in res.answer.claims:
        print("CLAIM:", c.text)
    print("UNCERT:", res.answer.uncertainty)

asyncio.run(main())
