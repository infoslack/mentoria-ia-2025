import json
import os
from openai import OpenAI
from pydantic import BaseModel, Field

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def search_kb(question):
    """Busca respostas na base de conhecimento"""
    with open("kb.json", "r", encoding="utf-8") as f:
        return json.load(f)


tools = [
    {
        "type": "function",
        "name": "search_kb",
        "description": "Search the knowledge base for answers",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The user's question"},
            },
            "required": ["question"],
        },
    }
]


# Response model
class KBResponse(BaseModel):
    answer: str = Field(description="Answer to the user's question")
    confidence: str = Field(description="Confidence level: high, medium, or low")


def answer_question(question):
    system_prompt = """
    Você é um assistente virtual de uma loja online brasileira.
    Responda usando apenas as informações da base de conhecimento.
    Se a pergunta não puder ser respondida com a base, informe educadamente.
    """

    # First call to check if model wants to use the tool
    response = client.responses.create(
        model="gpt-4o-mini",
        input=f"{system_prompt}\n\nPergunta: {question}",
        tools=tools,
    )

    # Check for function calls
    function_calls = [
        output for output in response.output if output.type == "function_call"
    ]

    if function_calls:
        # Get KB data and generate structured response
        function_call = function_calls[0]
        args = json.loads(function_call.arguments)
        kb_data = search_kb(args.get("question"))

        final_response = client.responses.parse(
            model="gpt-4o-mini",
            input=f"""
            {system_prompt}

            Pergunta: {question}

            Base de conhecimento:
            {json.dumps(kb_data, ensure_ascii=False)}
            """,
            instructions="Provide structured answer based on KB data",
            text_format=KBResponse,
        )

        return final_response.output[0].content[0].parsed
    else:
        # Direct answer if no tool called
        direct_text = next(
            (output.value for output in response.output if hasattr(output, "value")),
            next(
                (
                    output.content
                    for output in response.output
                    if hasattr(output, "content")
                ),
                "",
            ),
        )

        return KBResponse(answer=direct_text, confidence="low")


# Examples
question1 = "Qual é a política de devoluções da loja?"
response1 = answer_question(question1)
print(f"\n----- {question1}")
print(f"Resposta: {response1.answer}")
print(f"Confiança: {response1.confidence}")

question2 = "Vocês entregam para o Nordeste?"
response2 = answer_question(question2)
print(f"\n----- {question2}")
print(f"Resposta: {response2.answer}")
print(f"Confiança: {response2.confidence}")

question3 = "Qual a capital da frança?"
response3 = answer_question(question3)
print(f"\n----- {question3}")
print(f"Resposta: {response3.answer}")
print(f"Confiança: {response3.confidence}")
