import re
with open('aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad_str = '''    # A correction can also introduce a genuinely new fact.
    existing_keys = {" ".join(sorted(tokenize(c.text)))[:160] for c in new_claims}
    for scored in evidence[:2]:
        text = _best_sentence(scored.chunk.text, new_info)
        key = " ".join(sorted(tokenize(text)))[:160]
        if key in existing_keys:
            continue
        chunk_ids, citations, confidence, uncertain = verify_claim(
            text, evidence, engine
        )
        if uncertain or not citations:
            continue
        if any(
            cosine_sim(embed_one(text), embed_one(c.text)) > 0.8 for c in new_claims
        ):
            continue
        tmp = AnswerState(session_id=session_id, claims=new_claims)
        claim_id = _next_claim_id(tmp)
        new_claims.append(
            Claim(
                claim_id=claim_id,
                text=text,
                citations=citations,
                chunk_ids=chunk_ids,
                status=f"added_in_v{version}",
                confidence=confidence,
                is_uncertain=False,
            )
        )'''

content = content.replace(bad_str, "")

with open('aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched synthesis.py")
