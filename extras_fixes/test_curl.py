import urllib.request, json
data = {
    "model": "llama3.1:8b",
    "messages": [
        {"role": "system", "content": "You are an AI."},
        {"role": "user", "content": "Say Hello"}
    ],
    "stream": False
}
req = urllib.request.Request("http://127.0.0.1:11434/api/chat", data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    print(resp.read().decode())
