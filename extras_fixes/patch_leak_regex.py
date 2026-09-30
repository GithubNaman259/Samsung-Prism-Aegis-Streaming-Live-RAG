import re

with open('aegis/aegis/backend/synthesis.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Use regex to remove everything from "# A correction can also introduce" up to the end of patch_answer
pattern = re.compile(r'# A correction can also introduce a genuinely new fact\..*?return SynthesisOutput\(', re.DOTALL)
content, count = pattern.subn('return SynthesisOutput(', content)

with open('aegis/aegis/backend/synthesis.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Replaced {count} occurrences.")
