from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from openai import OpenAI
import requests
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = "gpt-4o-mini"
RAG_API_URL = "http://localhost:8000/search"

# --------------------------------------------------------------
# Step 1: Define routing and workflow data models
# --------------------------------------------------------------


class LegalRequestType(BaseModel):
    """Router LLM call: Determine the type of legal consultation"""

    request_type: Literal["consulta_interpretacao", "analise_caso", "other"] = Field(
        description="Tipo de consulta jurídica identificada"
    )

    confidence_score: float = Field(
        description="Confiança na classificação entre 0 e 1"
    )
    legal_area: str = Field(description="Área do direito identificada")
    description: str = Field(description="Descrição limpa e estruturada da consulta")


class RAGDocument(BaseModel):
    """Structure for RAG API response documents"""

    page_content: str
    metadata: Dict[str, Any]


class RAGResponse(BaseModel):
    """Structure for RAG API response"""

    results: List[RAGDocument]


class InterpretationQuery(BaseModel):
    """Details for legal interpretation queries"""

    legal_concepts: List[str] = Field(
        description="Conceitos jurídicos a serem interpretados"
    )
    search_queries: List[str] = Field(
        description="Queries otimizadas para busca no RAG"
    )
    context_needed: str = Field(
        description="Contexto adicional necessário para interpretação"
    )


class CaseAnalysisQuery(BaseModel):
    """Details for case analysis queries"""

    case_facts: str = Field(description="Fatos do caso apresentado")
    legal_issues: List[str] = Field(description="Questões jurídicas identificadas")
    search_queries: List[str] = Field(
        description="Queries para buscar precedentes e doutrina"
    )
    analysis_scope: str = Field(description="Escopo da análise solicitada")


class LegalResponse(BaseModel):
    """Final structured legal response"""

    success: bool = Field(description="Se a consulta foi processada com sucesso")
    response_type: str = Field(description="Tipo de resposta fornecida")
    main_answer: str = Field(description="Resposta principal à consulta")
    legal_foundation: str = Field(description="Fundamentação jurídica")
    sources_cited: List[str] = Field(description="Fontes citadas")
    recommendations: Optional[str] = Field(description="Recomendações adicionais")


# --------------------------------------------------------------
# Step 2: Define routing and RAG integration functions
# --------------------------------------------------------------


def route_legal_request(user_input: str) -> LegalRequestType:
    """Router LLM call to determine the type of legal consultation"""

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": """Analise a consulta jurídica e classifique em uma das categorias:
                - consulta_interpretacao: Perguntas sobre interpretação de normas, regulamentos ou conceitos jurídicos
                - analise_caso: Análise de situação específica com fatos concretos
                - other: Outros tipos de consulta
                
                Identifique também a área do direito e forneça uma descrição estruturada.""",
            },
            {"role": "user", "content": user_input},
        ],
        response_format=LegalRequestType,
    )

    return completion.choices[0].message.parsed


def search_rag_documents(search_query: str, limit: int = 5) -> RAGResponse:
    """Query the RAG API to retrieve relevant documents"""

    try:
        payload = {"query": search_query, "limit": limit}
        response = requests.post(RAG_API_URL, json=payload, timeout=30)
        response.raise_for_status()
        return RAGResponse(**response.json())

    except requests.exceptions.RequestException:
        return RAGResponse(results=[])


# --------------------------------------------------------------
# Step 3: Define workflow handlers for each legal request type
# --------------------------------------------------------------


def handle_interpretation_query(description: str, legal_area: str) -> LegalResponse:
    """Process legal interpretation queries"""

    # Extract interpretation details
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": f"Analise esta consulta de interpretação jurídica na área de {legal_area}. Identifique conceitos específicos e prepare queries de busca.",
            },
            {"role": "user", "content": description},
        ],
        response_format=InterpretationQuery,
    )

    query_details = completion.choices[0].message.parsed

    # Search for relevant documents using multiple queries
    all_documents = []
    for search_query in query_details.search_queries[:2]:  # Limit to 2 searches
        documents = search_rag_documents(search_query)
        all_documents.extend(documents.results)

    # Generate interpretation response
    documents_context = "\n".join(
        [f"Documento: {doc.page_content}" for doc in all_documents[:5]]
    )

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": f"""Você é um especialista em {legal_area}. Forneça uma interpretação jurídica clara e fundamentada.
                Conceitos a interpretar: {", ".join(query_details.legal_concepts)}
                Contexto adicional: {query_details.context_needed}""",
            },
            {
                "role": "user",
                "content": f"Consulta: {description}\n\nDocumentos relevantes:\n{documents_context}",
            },
        ],
        response_format=LegalResponse,
    )

    result = completion.choices[0].message.parsed
    result.response_type = "Interpretação Jurídica"
    return result


def handle_case_analysis(description: str, legal_area: str) -> LegalResponse:
    """Process case analysis queries"""

    # Extract case details
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": f"Analise este caso jurídico na área de {legal_area}. Identifique fatos, questões jurídicas e prepare busca por precedentes.",
            },
            {"role": "user", "content": description},
        ],
        response_format=CaseAnalysisQuery,
    )

    case_details = completion.choices[0].message.parsed

    # Search for precedents and doctrine
    all_documents = []
    for search_query in case_details.search_queries[:3]:  # Limit to 3 searches
        documents = search_rag_documents(search_query)
        all_documents.extend(documents.results)

    # Generate case analysis
    documents_context = "\n".join(
        [f"Precedente/Doutrina: {doc.page_content}" for doc in all_documents[:6]]
    )

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": f"""Você é um advogado especialista em {legal_area}. Analise o caso fornecido.
                Fatos do caso: {case_details.case_facts}
                Questões jurídicas: {", ".join(case_details.legal_issues)}
                Escopo da análise: {case_details.analysis_scope}""",
            },
            {
                "role": "user",
                "content": f"Caso: {description}\n\nPrecedentes e doutrina:\n{documents_context}",
            },
        ],
        response_format=LegalResponse,
    )

    result = completion.choices[0].message.parsed
    result.response_type = "Análise de Caso"
    return result


# --------------------------------------------------------------
# Step 4: Main workflow processing function
# --------------------------------------------------------------


def process_legal_consultation(user_input: str) -> Optional[LegalResponse]:
    """Main function implementing the legal consultation routing workflow"""

    # Route the request
    route_result = route_legal_request(user_input)

    # Check confidence threshold
    if route_result.confidence_score < 0.7:
        return None

    # Route to appropriate workflow handler
    if route_result.request_type == "consulta_interpretacao":
        return handle_interpretation_query(
            route_result.description, route_result.legal_area
        )
    elif route_result.request_type == "analise_caso":
        return handle_case_analysis(route_result.description, route_result.legal_area)
    else:
        return None


def format_legal_response(response: LegalResponse) -> str:
    """Format the legal response for display"""
    formatted = f"""
CONSULTA JURÍDICA - {response.response_type.upper()}

RESPOSTA PRINCIPAL:
{response.main_answer}

FUNDAMENTAÇÃO JURÍDICA:
{response.legal_foundation}

FONTES CITADAS:
"""
    for i, source in enumerate(response.sources_cited, 1):
        formatted += f"{i}. {source}\n"

    if response.recommendations:
        formatted += f"\nRECOMENDAÇÕES:\n{response.recommendations}"

    return formatted


# --------------------------------------------------------------
# Step 5: Test different types of legal consultations
# --------------------------------------------------------------

if __name__ == "__main__":
    # Test case 1: Legal interpretation query
    interpretation_query = (
        "O que deve conter na placa quando o profissional não for diplomado?"
    )

    print("=" * 80)
    print("TESTE 1: CONSULTA DE INTERPRETAÇÃO")
    print("=" * 80)
    print(f"Pergunta: {interpretation_query}")
    print("-" * 80)

    result1 = process_legal_consultation(interpretation_query)
    if result1:
        print(format_legal_response(result1))
    else:
        print("Consulta não foi processada com sucesso.")

    print("\n" + "=" * 80)

    # Test case 2: Case analysis
    case_analysis_query = "Minha empresa foi multada por não ter engenheiro responsável na obra. A obra já estava 80% concluída quando começou a fiscalização. Posso contestar essa multa?"

    print("TESTE 2: ANÁLISE DE CASO")
    print("=" * 80)
    print(f"Pergunta: {case_analysis_query}")
    print("-" * 80)

    result2 = process_legal_consultation(case_analysis_query)
    if result2:
        print(format_legal_response(result2))
    else:
        print("Consulta não foi processada com sucesso.")

    print("\n" + "=" * 80)

    # Test case 3: Non-legal query
    non_legal_query = "Qual é a receita do bolo de chocolate?"

    print("TESTE 3: CONSULTA NÃO-JURÍDICA")
    print("=" * 80)
    print(f"Pergunta: {non_legal_query}")
    print("-" * 80)

    result3 = process_legal_consultation(non_legal_query)
    if result3:
        print(format_legal_response(result3))
    else:
        print("Esta pergunta não foi identificada como uma consulta jurídica válida.")
