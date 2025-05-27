from openai import OpenAI
from langsmith.wrappers import wrap_openai
from langsmith import traceable
from dotenv import load_dotenv

load_dotenv("../.env")

client = wrap_openai(OpenAI())


@traceable
def main():
    response = client.responses.create(
        model="gpt-4o-mini",
        input="Explique em lista o que é machine learning",
    )

    print(response.output_text)


main()
