import re

with open(r'aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad = '''    if llm_sub_evidence:
        # MASSIVE FIX: Pass the specific sub-query (sq) to the LLM instead of the entire multi-intent utterance!
        # If the LLM sees the whole utterance but only gets evidence for one sub-query, it hallucinates uncertainty!
        tasks = [_llm_claims(sq, [(sq, ev)], llm, usage) for sq, ev in llm_sub_evidence]
        outcomes = await asyncio.gather(*tasks)
        for out in outcomes:
            if out:
                claim_specs.extend(out[0])
                uncertainty_acc.extend(out[1])'''

good = '''    if llm_sub_evidence:
        # Sequential processing to prevent overloading the local Ollama instance
        for sq, ev in llm_sub_evidence:
            out = await _llm_claims(sq, [(sq, ev)], llm, usage)
            if out:
                claim_specs.extend(out[0])
                uncertainty_acc.extend(out[1])'''

if bad in content:
    content = content.replace(bad, good)
    print("Patched sequential")
else:
    print("Could not find bad block")

with open(r'aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)
