import re

with open(r'aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad = '''                if has_new_constraint:
                    cand_nums = [int(n) for n in re.findall(r"\d+", candidate)]
                    if any(n >= req_num for n in cand_nums):
                        # Ensure semantic relevance and context match
                        if cand_sim < 0.25:
                            continue
                        if ("people" in new_lower or "capacity" in new_lower or "seats" in new_lower):
                            if not ("people" in candidate.lower() or "seats" in candidate.lower() or "capacity" in candidate.lower()):
                                continue
                        replacement_text = candidate
                        found_satisfying_evidence = True
                        break
                else:
                    if cand_sim < 0.25:
                        continue
                    replacement_text = candidate
                    found_satisfying_evidence = True
                    break'''

good = '''                if has_new_constraint:
                    cand_nums = [int(n) for n in re.findall(r"\d+", candidate)]
                    if any(n >= req_num for n in cand_nums):
                        # Relax the cosine similarity guard if it satisfies the explicit numeric constraint AND the lexical context matches
                        if ("people" in new_lower or "capacity" in new_lower or "seats" in new_lower):
                            if not ("people" in candidate.lower() or "seats" in candidate.lower() or "capacity" in candidate.lower()):
                                continue
                        elif cand_sim < 0.15:
                            continue
                            
                        replacement_text = candidate
                        found_satisfying_evidence = True
                        break
                else:
                    if cand_sim < 0.15:
                        continue
                    replacement_text = candidate
                    found_satisfying_evidence = True
                    break'''

if bad in content:
    content = content.replace(bad, good)
    print("Patched successfully")
else:
    print("Could not find bad block")

with open(r'aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)
