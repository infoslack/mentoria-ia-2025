from openai import OpenAI
from dotenv import load_dotenv
import guardrails as gd
from guardrails.validators import (
    FailResult,
    PassResult,
    register_validator,
    ValidationResult,
    Validator,
)
from typing import Dict, Any
import warnings
import os

# Suprime warnings do tqdm e asyncio
warnings.filterwarnings("ignore", category=UserWarning, module="tqdm.auto")
warnings.filterwarnings("ignore", message="Could not obtain an event loop")
os.environ["TQDM_DISABLE"] = "1"

load_dotenv("../.env")

client = OpenAI()

# Exemplo sem guardrails
print("=== Sem Guardrails ===")
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Qual a capital da França?"}],
)
print(f"Resposta: {response.choices[0].message.content}\n")


# Validador customizado para ml/ia
@register_validator(name="ml-topic-validator", data_type="string")
class MLTopicValidator(Validator):
    """Validador que permite apenas tópicos de ML/IA"""

    def __init__(self, on_fail="exception"):
        super().__init__(on_fail=on_fail)

    def _validate(self, value: Any, metadata: Dict) -> ValidationResult:
        text_lower = str(value).lower()

        # Keywords de ml/ia
        ml_keywords = [
            "machine learning",
            "ml",
            "ia",
            "inteligência artificial",
            "artificial intelligence",
            "ai",
            "deep learning",
            "neural",
            "tensorflow",
            "pytorch",
            "algoritmo",
            "modelo",
            "training",
        ]

        # Keywords bloqueadas
        blocked_keywords = [
            "capital",
            "país",
            "cidade",
            "geografia",
            "frança",
            "paris",
            "receita",
            "pizza",
            "futebol",
            "esporte",
        ]

        # Verifica bloqueios primeiro
        for blocked in blocked_keywords:
            if blocked in text_lower:
                return FailResult(
                    error_message=f"Tópico '{blocked}' não permitido. Use apenas ML/IA."
                )

        # Verifica se é sobre ml/ia
        if not any(ml_word in text_lower for ml_word in ml_keywords):
            return FailResult(
                error_message="Por favor, faça perguntas sobre Machine Learning ou IA."
            )

        return PassResult()


# Função para chamar openai
def ask_openai(
    prompt: str, *, instructions: str = None, msg_history: list = None, **kwargs
) -> str:
    """Wrapper para OpenAI com argumentos keyword-only conforme recomendado"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
    )
    return response.choices[0].message.content


# Usando guardrails
print("=== Com Guardrails ===")

# Cria o guard com validador
guard = gd.Guard().use(MLTopicValidator(), on="prompt")

# Testes
test_prompts = [
    "O que é deep learning?",
    "Como funciona uma rede neural?",
    "Qual a capital da França?",
]

for prompt in test_prompts:
    print(f"\nPergunta: '{prompt}'")

    try:
        result = guard(ask_openai, prompt=prompt)
        print(f"✅ Resposta: {result.validated_output[:80]}...")
    except Exception as e:
        print(f"❌ Bloqueado: {str(e)}")
