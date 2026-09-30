import urllib.request, json
data = {
    "model": "llama3.1:8b",
    "messages": [
        {"role": "system", "content": "Return ONLY JSON."},
        {"role": "user", "content": "Give me a JSON object with a 'hello' key."}
    ],
    "stream": False,
    "format": "json"
}
req = urllib.request.Request("http://127.0.0.1:11434/api/chat", data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    print(resp.read().decode())
