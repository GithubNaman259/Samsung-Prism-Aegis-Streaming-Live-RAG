with open('aegis/aegis/backend/llm.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('os.getenv("AEGIS_OLLAMA_MODEL", "llama3.1:8b")', '"llama3.1:8b"')

with open('aegis/aegis/backend/llm.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Hardcoded Llama 3.1 8B")
