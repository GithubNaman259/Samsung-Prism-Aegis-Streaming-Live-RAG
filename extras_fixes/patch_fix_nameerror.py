import re

with open('aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad_str = "    return SynthesisOutput(patched, changed, usage, evidence)"

good_str = '''    patched = AnswerState(
        session_id=session_id,
        claims=new_claims,
        uncertainty=list(set(state.uncertainty + new_uncertainties)),
        answer_version=version,
    )
    return SynthesisOutput(patched, changed, usage, evidence)'''

content = content.replace(bad_str, good_str)

with open('aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Restored patched definition.")
