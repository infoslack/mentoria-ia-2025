from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from openai import OpenAI
import requests
import os
import logging

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = "gpt-4o-mini"
RAG_API_URL = "http://localhost:8000/search"


class QueryAnalysis(BaseModel):
    """First LLM call: Analyze legal query and extract key concepts"""

    legal_area: str = Field(
        description="Area do direito identificada (ex: direito profissional, direito administrativo)"
    )
    key_concepts: List[str] = Field(
        description="Conceitos jurídicos principais identificados na pergunta"
    )
    search_query: str = Field(description="Query otimizada para busca no sistema RAG")
    is_legal_question: bool = Field(description="Se a pergunta é de natureza jurídica")
    confidence_score: float = Field(description="Confiança na análise entre 0 e 1")


class RAGDocument(BaseModel):
    """Structure for RAG API response documents"""

    page_content: str
    metadata: Dict[str, Any]


class RAGResponse(BaseModel):
    """Structure for RAG API response"""

    results: List[RAGDocument]


class LegalResponse(BaseModel):
    """Third LLM call: Generate structured legal response"""

    direct_answer: str = Field(description="Resposta direta e objetiva à pergunta")
    legal_foundation: str = Field(
        description="Fundamentação jurídica baseada nos documentos"
    )
    cited_sources: List[str] = Field(description="Lista das fontes citadas")
    additional_considerations: Optional[str] = Field(
        description="Considerações adicionais relevantes"
    )


def analyze_legal_query(user_question: str) -> QueryAnalysis:
    """First LLM call: Analyze the legal question and prepare search strategy"""
    logger.info("Starting legal query analysis")
    logger.debug(f"User question: {user_question}")

    response = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": """Você é um assistente especializado em análise de consultas jurídicas. 
                Analise a pergunta do usuário e identifique:
                1. A área do direito envolvida
                2. Os conceitos jurídicos principais
                3. Formule uma query de busca otimizada para encontrar informações relevantes
                4. Determine se é realmente uma pergunta jurídica válida""",
            },
            {
                "role": "user",
                "content": f"Analise esta consulta jurídica: '{user_question}'",
            },
        ],
        response_format=QueryAnalysis,
    )

    result = response.choices[0].message.parsed
    logger.info(
        f"Analysis complete - Legal area: {result.legal_area}, Confidence: {result.confidence_score:.2f}"
    )
    logger.debug(f"Key concepts: {', '.join(result.key_concepts)}")
    logger.debug(f"Search query: {result.search_query}")

    return result


def search_rag_documents(search_query: str, limit: int = 5) -> RAGResponse:
    """Second step: Query the RAG API to retrieve relevant documents"""
    logger.info("Searching RAG documents")
    logger.debug(f"Search query: {search_query}")

    try:
        payload = {"query": search_query, "limit": limit}

        response = requests.post(RAG_API_URL, json=payload, timeout=30)
        response.raise_for_status()

        rag_response = RAGResponse(**response.json())
        logger.info(f"Retrieved {len(rag_response.results)} documents from RAG")

        return rag_response

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling RAG API: {e}")
        # Return empty response in case of API failure
        return RAGResponse(results=[])
    except Exception as e:
        logger.error(f"Unexpected error in RAG search: {e}")
        return RAGResponse(results=[])


def generate_legal_response(
    original_question: str, query_analysis: QueryAnalysis, rag_documents: RAGResponse
) -> LegalResponse:
    """Third LLM call: Generate comprehensive legal response"""
    logger.info("Generating legal response")

    # Prepare documents context
    documents_context = ""
    for i, doc in enumerate(rag_documents.results, 1):
        documents_context += f"\nDocumento {i}:\n{doc.page_content}\n"
        if doc.metadata:
            documents_context += f"Metadados: {doc.metadata}\n"

    system_prompt = f"""Você é um advogado especializado em {query_analysis.legal_area}. 
    Com base nos documentos fornecidos, responda à consulta jurídica de forma clara e fundamentada.
    
    Estruture sua resposta da seguinte forma:
    1. Resposta direta e objetiva
    2. Fundamentação jurídica baseada nos documentos
    3. Fontes citadas
    4. Considerações adicionais se relevantes
    
    Seja preciso, use linguagem jurídica apropriada, e cite especificamente os trechos relevantes dos documentos."""

    user_content = f"""Pergunta original: {original_question}
    
    Conceitos identificados: {", ".join(query_analysis.key_concepts)}
    
    Documentos recuperados:{documents_context}
    
    Por favor, responda à consulta jurídica com base nesses documentos."""

    response = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        response_format=LegalResponse,
    )

    result = response.choices[0].message.parsed
    logger.info("Legal response generated successfully")

    return result


def process_legal_consultation(user_question: str) -> Optional[LegalResponse]:
    """Main function implementing the legal consultation prompt chain"""
    logger.info("Processing legal consultation")
    logger.debug(f"Original question: {user_question}")

    # First LLM call: Analyze the legal query
    query_analysis = analyze_legal_query(user_question)

    # Gate check: Verify if it's a valid legal question with sufficient confidence
    if not query_analysis.is_legal_question or query_analysis.confidence_score < 0.7:
        logger.warning(
            f"Gate check failed - is_legal_question: {query_analysis.is_legal_question}, "
            f"confidence: {query_analysis.confidence_score:.2f}"
        )
        return None

    logger.info("Gate check passed, proceeding with document search")

    # Second step: Search relevant documents in RAG
    rag_documents = search_rag_documents(query_analysis.search_query)

    if not rag_documents.results:
        logger.warning("No documents found in RAG search")
        # You could return a response indicating no relevant documents were found
        # For now, we'll continue with empty results

    # Third LLM call: Generate legal response
    legal_response = generate_legal_response(
        user_question, query_analysis, rag_documents
    )

    logger.info("Legal consultation processing completed successfully")
    return legal_response


def format_legal_response(response: LegalResponse) -> str:
    """Format the legal response for display"""
    formatted = f"""
RESPOSTA JURÍDICA:

{response.direct_answer}

FUNDAMENTAÇÃO LEGAL:
{response.legal_foundation}

FONTES CITADAS:
"""
    for i, source in enumerate(response.cited_sources, 1):
        formatted += f"{i}. {source}\n"

    if response.additional_considerations:
        formatted += (
            f"\nCONSIDERAÇÕES ADICIONAIS:\n{response.additional_considerations}"
        )

    return formatted


# Example usage
if __name__ == "__main__":
    # Test case 1: Valid legal question
    question1 = "O que deve conter na placa quando o profissional não for diplomado?"

    print("=" * 80)
    print("CONSULTA JURÍDICA 1")
    print("=" * 80)
    print(f"Pergunta: {question1}")
    print("-" * 80)

    result1 = process_legal_consultation(question1)
    if result1:
        print(format_legal_response(result1))
    else:
        print("Esta pergunta não foi identificada como uma consulta jurídica válida.")

    print("\n" + "=" * 80)

    # Test case 2: Non-legal question
    question2 = "Qual é a receita do bolo de chocolate?"

    print("CONSULTA JURÍDICA 2")
    print("=" * 80)
    print(f"Pergunta: {question2}")
    print("-" * 80)

    result2 = process_legal_consultation(question2)
    if result2:
        print(format_legal_response(result2))
    else:
        print("Esta pergunta não foi identificada como uma consulta jurídica válida.")
