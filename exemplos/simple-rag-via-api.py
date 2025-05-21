import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

RAG_ENDPOINT = "http://localhost:8000/search"


def rag_query(query, top_k=3):
    # Em vez de usar o cliente Qdrant, fazemos uma chamada HTTP para o endpoint da API
    payload = {"query": query, "limit": top_k}

    response = requests.post(RAG_ENDPOINT, json=payload)

    if response.status_code != 200:
        raise Exception(f"Erro na requisição: {response.status_code} - {response.text}")

    search_results = response.json()["results"]

    # Construir o contexto a partir dos resultados
    context = ""
    retrieved_documents = []

    for i, result in enumerate(search_results):
        # Extrair o texto do documento do campo page_content
        doc_text = result["page_content"]
        # Extrair metadados para uso posterior
        metadata = result.get("metadata", {})

        context += f"Documento {i + 1}: {doc_text}\n\n"
        retrieved_documents.append({"document": doc_text, "metadata": metadata})

    # Gerar resposta com a OpenAI usando a API responses.create
    openai_client = OpenAI()

    prompt = f"""
    Com base nos seguintes documentos, responda à pergunta.
    
    Documentos: {context}
    
    Pergunta: {query}
    """

    response = openai_client.responses.create(
        model="gpt-4o-mini",
        input=prompt,
        temperature=0,
    )

    answer = response.output_text

    return {
        "query": query,
        "retrieved_documents": retrieved_documents,
        "context": context,
        "response": answer,
    }


# Executar a consulta
query = "O que deve conter na placa quando o profissional não for diplomado?"
results = rag_query(query)
print(results["response"])

# Análise extra dos resultados
print(f"\nConsulta: {results['query']}")
print("\nDocumentos recuperados:")
for i, doc in enumerate(results["retrieved_documents"]):
    print(
        f"{i + 1}. {doc['document'][:150]}..."
    )  # Mostra apenas os primeiros 150 caracteres
    if "metadata" in doc and doc["metadata"]:
        print(f"   Metadados: {doc['metadata']}")
