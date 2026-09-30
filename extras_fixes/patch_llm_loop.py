import re
with open('aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad_str = '''    llm_out = (
        None
        if needs_deterministic_grounding
        else await _llm_claims(
            utterance,
            sub_query_evidence,
            llm,
            usage,
        )
    )'''

good_str = '''    claim_specs = []
    uncertainty_acc = []
    if not needs_deterministic_grounding:
        for sq_ev in sub_query_evidence:
            out = await _llm_claims(utterance, [sq_ev], llm, usage)
            if out:
                claim_specs.extend(out[0])
                uncertainty_acc.extend(out[1])
        llm_out = (claim_specs, uncertainty_acc) if (claim_specs or uncertainty_acc) else None
    else:
        llm_out = None'''

content = content.replace(bad_str, good_str)
with open('aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched LLM loop")
