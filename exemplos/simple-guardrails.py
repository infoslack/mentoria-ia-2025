from nemoguardrails import LLMRails, RailsConfig
from openai import OpenAI
import nest_asyncio

# Aplicar nest_asyncio para resolver problemas de loop assíncrono
nest_asyncio.apply()

print("\n=== SEM GUARDRAILS ===\n")

client = OpenAI()
response = client.responses.create(
    model="gpt-4o-mini",
    input="Explique em lista o que é machine learning",
)
print(response.output_text)


print("=== COM NEMO GUARDRAILS ===\n")
config = RailsConfig.from_path("./config")
rails = LLMRails(config)

response = rails.generate(
    messages=[{"role": "user", "content": "O que é machine learning?"}]
)
print(f"Pergunta sobre ML:\n{response['content']}\n")

response = rails.generate(
    messages=[{"role": "user", "content": "Qual a capital da França?"}]
)
print(f"Pergunta off-topic:\n{response['content']}\n")
