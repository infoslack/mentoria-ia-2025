import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


response = client.responses.create(
    model="gpt-4o-mini",
    input="Extraia informações do evento: Daniel e Geanderson vão gravar uma aula na terça-feira.",
)

print(response.output_text)
