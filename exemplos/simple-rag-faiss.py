import faiss
from sentence_transformers import SentenceTransformer
from openai import OpenAI
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

model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
)

document_embeddings = model.encode(documents)
print(f"Embedding dimension: {document_embeddings.shape[1]}")

index = faiss.IndexFlatL2(document_embeddings.shape[1])
index.add(document_embeddings.astype("float32"))
print(f"Index contém {index.ntotal} vectors")


def retrieve(query, top_k=3):
    query_vector = model.encode([query]).astype("float32")
    distances, indices = index.search(query_vector, top_k)

    results = []
    for i, idx in enumerate(indices[0]):
        results.append({"document": documents[idx], "distance": distances[0][i]})

    return results


def rag_query(query, top_k=3):
    results = retrieve(query, top_k)

    context = ""
    for i in range(len(results)):
        context += f"Documento {i + 1}: {results[i]['document']}\n\n"

    client = OpenAI()

    prompt = f"""
    Com base nos seguintes documentos, responda à pergunta.
    
    Documentos: {context}
    
    Pergunta: {query}
    """

    response = client.responses.create(model="gpt-4o-mini", input=prompt, temperature=0)

    answer = response.output_text

    return {
        "query": query,
        "retrieved_documents": results,
        "context": context,
        "response": answer,
    }


query = "Como funciona o RAG?"
results = rag_query(query)

results

print(f"\nConsulta: {results['query']}")
print("\nDocumentos recuperados:")
for i, doc in enumerate(results["retrieved_documents"]):
    print(f"{i + 1}. {doc['document']} (Pontuação: {doc['distance']:.4f})")

print(f"\nResposta da OpenAI: {results['response']}")
