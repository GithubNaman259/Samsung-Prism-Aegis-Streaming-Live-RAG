import json
with open(r'C:\Users\menks\.gemini\antigravity\brain\cadae330-1624-43fc-a7b0-8edccf692244\.system_generated\logs\transcript_full.jsonl', 'r') as f:
    for line in f:
        obj = json.loads(line)
        if 'tool_calls' in obj:
            for tc in obj['tool_calls']:
                if tc['name'] == 'run_command':
                    cmd = tc['args'].get('CommandLine', '')
                    if 'synthesis.py' in cmd:
                        print("================================")
                        print(cmd)
