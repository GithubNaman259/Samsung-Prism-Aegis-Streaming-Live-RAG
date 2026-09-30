import sys
sys.path.append('A:\\Aegis_Fixed_Clean_Release_v2\\aegis')
from aegis.backend.llm import LLMClient
import urllib.request, json

class MyClient(LLMClient):
    def _ollama_available(self) -> bool:
        try:
            req = urllib.request.Request(
                f"{self.ollama_url.rstrip('/')}/api/tags", method="GET"
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                if not (200 <= resp.status < 300):
                    print("Bad status:", resp.status)
                    return False
                payload = json.loads(resp.read().decode("utf-8"))
                names = {
                    str(x.get("name", ""))
                    for x in payload.get("models", [])
                    if isinstance(x, dict)
                }
                print("Models seen:", names)
                print("Looking for:", self.ollama_model)
                return self.ollama_model in names
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False

client = MyClient()
print("Provider:", client.provider)
print("Available?", client._ollama_available())
