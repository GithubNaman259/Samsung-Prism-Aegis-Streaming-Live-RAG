import json, re

with open(r'C:\Users\menks\.gemini\antigravity\brain\f4a81504-f5b4-45b6-8f58-06c0823b5da8\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        if obj.get('type') == 'USER_INPUT':
            content = obj.get('content', '')
            for target in ['find a venue', 'restaurant', 'actually', 'accommodate', 'cancellation', 'policy', 'rewrite', 'Mumbai', 'Pune', '500']:
                if target in content:
                    lines = content.split('\n')
                    for l in lines:
                        if any(k in l for k in ['find a venue', 'restaurant for an event', 'actually', 'rewrite', 'dance floor', 'paternity', 'cancellation policy']):
                            print(l.strip())
