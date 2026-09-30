import urllib.request
try:
    req = urllib.request.Request("http://127.0.0.1:11434/api/tags", method="GET")
    with urllib.request.urlopen(req, timeout=5.0) as resp:
        print("Status:", resp.status)
        import json
        payload = json.loads(resp.read().decode())
        names = {x.get("name") for x in payload.get("models", []) if isinstance(x, dict)}
        print("Models:", names)
        print("Is llama3.1:8b in names?", "llama3.1:8b" in names)
except Exception as e:
    print("Error:", e)
