import json
with open(r'C:\Users\menks\.gemini\antigravity\brain\f4a81504-f5b4-45b6-8f58-06c0823b5da8\.system_generated\logs\transcript_full.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        if 'tool_calls' in obj:
            for tc in obj['tool_calls']:
                if tc['name'] == 'run_command' and '.py' in tc['args'].get('CommandLine', ''):
                    print(tc['args']['CommandLine'][:200])
