import json
with open(r'C:\Users\menks\.gemini\antigravity\brain\cadae330-1624-43fc-a7b0-8edccf692244\.system_generated\logs\transcript.jsonl', 'r') as f:
    for line in f:
        obj = json.loads(line)
        if obj.get('source') == 'MODEL' and obj.get('type') == 'GENERIC':
            print("==== SUBAGENT TEXT ====")
            print(obj.get('content')[:500])
