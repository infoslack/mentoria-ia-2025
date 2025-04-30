from openai import OpenAI
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()

documents = [
    "FAISS é uma biblioteca para busca eficiente de similaridade desenvolvida pelo Facebook AI Research.",
    "RAG (Retrieval-Augmented Generation) é uma técnica que melhora os modelos de linguagem recuperando informações relevantes de uma base de conhecimento.",
    "Embeddings são representações vetoriais de texto que capturam significado semântico.",
    "Bancos de dados vetoriais como FAISS permitem buscas eficientes de similaridade em espaços de alta dimensão.",
    "A similaridade de cosseno entre dois vetores mede o cosseno do ângulo entre eles, fornecendo uma medida de sua similaridade.",
    "Transformers de sentenças são modelos especificamente projetados para criar embeddings de sentenças que capturam significado semântico.",
    "Chunking é o processo de dividir documentos longos em pedaços menores e mais gerenciáveis para processamento.",
    "Busca semântica usa significado em vez de palavras-chave para encontrar informações relevantes.",
    "Recuperação densa usa representações vetoriais densas de consultas e documentos para realizar a recuperação.",
    "Retrieval-Augmented Generation combina sistemas de recuperação com modelos generativos para produzir respostas mais precisas e factuais.",
]

# Inicializar o cliente Qdrant
client = QdrantClient(":memory:")  # Usando armazenamento em memória
collection_name = "documents_collection"

# Adicionar documentos diretamente usando a API simplificada
client.add(
    collection_name=collection_name,
    documents=documents,
    ids=list(range(len(documents))),
)

print(f"Coleção '{collection_name}' contém {len(documents)} documentos")


def rag_query(query, top_k=3):
    # Buscar documentos mais relevantes usando a API simplificada
    search_results = client.query(
        collection_name=collection_name, query_text=query, limit=top_k
    )

    # Construir o contexto a partir dos resultados
    context = ""
    retrieved_documents = []

    for i, result in enumerate(search_results):
        doc_text = result.document
        score = result.score
        context += f"Documento {i + 1}: {doc_text}\n\n"
        retrieved_documents.append({"document": doc_text, "score": score})

    # Gerar resposta com a OpenAI
    openai_client = OpenAI()

    prompt = f"""
    Com base nos seguintes documentos, responda à pergunta.
    
    Documentos: {context}
    
    Pergunta: {query}
    """

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    answer = response.choices[0].message.content

    return {
        "query": query,
        "retrieved_documents": retrieved_documents,
        "context": context,
        "response": answer,
    }


# Executar a consulta
query = "Como funciona o RAG?"
results = rag_query(query)

# Exibir resultados
print(f"\nConsulta: {results['query']}")
print("\nDocumentos recuperados:")
for i, doc in enumerate(results["retrieved_documents"]):
    print(f"{i + 1}. {doc['document']} (Score: {doc['score']:.4f})")

print(f"\nResposta da OpenAI: {results['response']}")
