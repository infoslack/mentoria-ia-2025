import requests
import json

# Configuração
API_URL = "http://localhost:8000/openai/stream"
QUERY = "O que deve conter na placa quando o profissional não for diplomado?"

# Faz a requisição
response = requests.post(API_URL, json={"query": QUERY, "limit": 5}, stream=True)

print(f"Pergunta: {QUERY}\n")
print("Resposta:\n")

# Processa o stream
for line in response.iter_lines():
    if line:
        line_str = line.decode("utf-8")
        if line_str.startswith("data: "):
            try:
                data = json.loads(line_str[6:])

                # Imprime apenas os deltas de texto
                if data["type"] == "text_delta":
                    print(data["delta"], end="", flush=True)

                # Mostra quando terminar
                elif data["type"] == "stream_completed":
                    print("\n\n✅ Resposta completa!")

            except json.JSONDecodeError:
                pass
