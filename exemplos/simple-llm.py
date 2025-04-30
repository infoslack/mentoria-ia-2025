from openai import OpenAI
from dotenv import load_dotenv

load_dotenv("../.env")

client = OpenAI()

response = client.responses.create(
    model="gpt-4o-mini",
    input="Explique em lista o que é machine learning",
)

print(response.output_text)
