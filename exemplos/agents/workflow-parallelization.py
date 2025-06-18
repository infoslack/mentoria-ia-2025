import asyncio
import os
import nest_asyncio
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from typing import List

nest_asyncio.apply()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = "gpt-4o-mini"

# --------------------------------------------------------------
# Step 1: Define validation models
# --------------------------------------------------------------


class LegalValidation(BaseModel):
    """Check if input is a valid legal consultation"""

    is_legal_consultation: bool = Field(
        description="Whether this is a legal consultation"
    )
    confidence_score: float = Field(description="Confidence score between 0 and 1")
    legal_area: str = Field(description="Identified legal area if applicable")


class EthicsCheck(BaseModel):
    """Check for ethical concerns in legal consultation"""

    is_ethical: bool = Field(description="Whether the consultation appears ethical")
    concerns: List[str] = Field(description="List of potential ethical concerns")
    risk_level: str = Field(description="Low, Medium, or High risk level")


class ComplexityAssessment(BaseModel):
    """Assess the complexity of the legal consultation"""

    complexity_level: str = Field(description="Simple, Moderate, or Complex")
    requires_specialist: bool = Field(
        description="Whether specialist consultation is needed"
    )


# --------------------------------------------------------------
# Step 2: Define parallel validation tasks
# --------------------------------------------------------------


async def validate_legal_consultation(user_input: str) -> LegalValidation:
    """Check if the input is a valid legal consultation"""
    completion = await client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Determine se esta é uma solicitação legítima de consulta jurídica e identifique a área do direito.",
            },
            {"role": "user", "content": user_input},
        ],
        response_format=LegalValidation,
    )
    return completion.choices[0].message.parsed


async def check_ethics(user_input: str) -> EthicsCheck:
    """Check for ethical concerns in the consultation"""
    completion = await client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": """Verifique preocupações éticas nesta solicitação de consulta jurídica.
                Considere: potenciais atividades ilegais, processos frívolos, conflitos de interesse,
                solicitações que poderiam prejudicar outros, ou consultas fora da prática jurídica ética.""",
            },
            {"role": "user", "content": user_input},
        ],
        response_format=EthicsCheck,
    )
    return completion.choices[0].message.parsed


async def assess_complexity(user_input: str) -> ComplexityAssessment:
    """Assess the complexity and resource requirements"""
    completion = await client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": """Avalie a complexidade desta consulta jurídica.
                Considere: número de questões jurídicas envolvidas, conhecimento especializado necessário,
                profundidade de pesquisa necessária, e se recomenda consulta com especialista.""",
            },
            {"role": "user", "content": user_input},
        ],
        response_format=ComplexityAssessment,
    )
    return completion.choices[0].message.parsed


# --------------------------------------------------------------
# Step 3: Main validation function
# --------------------------------------------------------------


async def validate_consultation_request(user_input: str) -> tuple[bool, dict]:
    """Run all validation checks in parallel"""

    # Execute all validations concurrently
    legal_check, ethics_check, complexity_check = await asyncio.gather(
        validate_legal_consultation(user_input),
        check_ethics(user_input),
        assess_complexity(user_input),
    )

    # Determine if consultation should proceed
    is_valid = (
        legal_check.is_legal_consultation
        and legal_check.confidence_score > 0.7
        and ethics_check.is_ethical
        and ethics_check.risk_level != "High"
    )

    # Prepare validation results summary
    validation_results = {
        "legal_validation": {
            "is_legal": legal_check.is_legal_consultation,
            "confidence": legal_check.confidence_score,
            "area": legal_check.legal_area,
        },
        "ethics_check": {
            "is_ethical": ethics_check.is_ethical,
            "concerns": ethics_check.concerns,
            "risk_level": ethics_check.risk_level,
        },
        "complexity": {
            "level": complexity_check.complexity_level,
            "needs_specialist": complexity_check.requires_specialist,
        },
    }

    return is_valid, validation_results


def print_validation_results(consultation: str, is_valid: bool, results: dict):
    """Print detailed validation results"""
    print(f"\nCONSULTA: {consultation}")
    print("=" * 80)
    print(f"VÁLIDA: {'SIM' if is_valid else 'NÃO'}")
    print("-" * 80)

    legal = results["legal_validation"]
    print(f"Validação Legal: {'✓' if legal['is_legal'] else '✗'}")
    print(f"  Confiança: {legal['confidence']:.2f}")
    print(f"  Área: {legal['area']}")

    ethics = results["ethics_check"]
    print(f"Verificação Ética: {'✓' if ethics['is_ethical'] else '✗'}")
    print(f"  Nível de Risco: {ethics['risk_level']}")
    if ethics["concerns"]:
        print(f"  Preocupações: {', '.join(ethics['concerns'])}")

    complexity = results["complexity"]
    print("Avaliação de Complexidade:")
    print(f"  Nível: {complexity['level']}")
    print(
        f"  Requer Especialista: {'Sim' if complexity['needs_specialist'] else 'Não'}"
    )


# --------------------------------------------------------------
# Step 4: Test examples
# --------------------------------------------------------------


async def run_examples():
    """Test different types of legal consultations"""

    # Test 1: Valid legal consultation
    valid_consultation = (
        "O que deve conter na placa quando o profissional não for diplomado?"
    )
    is_valid, results = await validate_consultation_request(valid_consultation)
    print_validation_results(valid_consultation, is_valid, results)

    # Test 2: Complex case analysis
    complex_case = "Minha empresa foi multada por não ter engenheiro responsável na obra. A obra já estava 80% concluída quando começou a fiscalização. Posso contestar essa multa e quais são os precedentes favoráveis?"
    is_valid, results = await validate_consultation_request(complex_case)
    print_validation_results(complex_case, is_valid, results)

    # Test 3: Potentially problematic consultation
    problematic_consultation = "Como posso esconder ativos da empresa para evitar pagar impostos sem ser descoberto pela Receita Federal?"
    is_valid, results = await validate_consultation_request(problematic_consultation)
    print_validation_results(problematic_consultation, is_valid, results)

    # Test 4: Non-legal question
    non_legal = "Qual é a receita do bolo de chocolate?"
    is_valid, results = await validate_consultation_request(non_legal)
    print_validation_results(non_legal, is_valid, results)


# --------------------------------------------------------------
# Step 5: Advanced validation with timing
# --------------------------------------------------------------


async def run_validation_with_timing():
    """Demonstrate performance benefits of parallel validation"""
    import time

    consultation = "Preciso de orientação sobre direitos trabalhistas para demissão de funcionário com mais de 10 anos de empresa"

    # Measure parallel execution time
    start_time = time.time()
    is_valid, results = await validate_consultation_request(consultation)
    parallel_time = time.time() - start_time

    print(f"\n{'=' * 80}")
    print("DEMONSTRAÇÃO DE PERFORMANCE - VALIDAÇÃO PARALELA")
    print(f"{'=' * 80}")
    print(f"Consulta processada em: {parallel_time:.2f} segundos")
    print(f"Resultado: {'VÁLIDA' if is_valid else 'INVÁLIDA'}")
    print(f"Área identificada: {results['legal_validation']['area']}")
    print(f"Complexidade: {results['complexity']['level']}")
    print(f"Risco ético: {results['ethics_check']['risk_level']}")


if __name__ == "__main__":
    # Run all examples
    asyncio.run(run_examples())

    # Demonstrate timing
    asyncio.run(run_validation_with_timing())
