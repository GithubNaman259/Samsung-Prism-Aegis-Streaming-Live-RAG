import sys
sys.path.append('A:\\Aegis_Fixed_Clean_Release_v2\\aegis')
from aegis.backend.llm import LLMClient
client = LLMClient()
print("Provider:", client.provider)
print("Available?", client._ollama_available())
