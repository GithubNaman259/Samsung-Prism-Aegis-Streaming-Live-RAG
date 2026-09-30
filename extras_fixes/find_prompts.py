import json, re

prompts = []
with open(r'C:\Users\menks\.gemini\antigravity\brain\f4a81504-f5b4-45b6-8f58-06c0823b5da8\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        if obj.get('type') == 'USER_INPUT':
            content = obj.get('content', '')
            matches = re.findall(r'(?:Ask Aegis|Ready)\s*\r?\n([^\r\n]+)', content)
            for m in matches:
                m_clean = m.strip()
                if m_clean and m_clean not in ['mic', 'Send', 'Enter to send', 'Ready']:
                    if m_clean not in prompts:
                        prompts.append(m_clean)

for i, p in enumerate(prompts, 1):
    print(f'{i}. {p}')
