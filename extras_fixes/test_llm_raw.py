import asyncio
from aegis.backend.retrieval.engine import get_engine
from aegis.backend.llm import get_client, extract_json

async def main():
    llm = get_client()
    prompt = '''Answer the request using ONLY the evidence assigned to each sub-query.
Request: "tell me about the domestic and the international travel booking policy"
SUB-QUERY:
tell me about the domestic travel booking policy
EVIDENCE:
[Doc_09#c1] (Doc_09) All domestic travel is booked through the corporate travel desk.

Return JSON:
{"claims": [{"text": "one factual sentence", "chunk_ids": ["Doc_99#c1"]}], "uncertainty": []}
'''
    resp = await llm.complete(system="You are an AI.", prompt=prompt, max_tokens=900)
    print("Raw LLM Text:")
    print(resp.text)
    print("Extracted JSON:", extract_json(resp.text))

asyncio.run(main())
