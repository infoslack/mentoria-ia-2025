import os
import uuid
from tqdm.auto import tqdm
from typing import List
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct
from fastembed.sparse.bm25 import Bm25
from fastembed.late_interaction import LateInteractionTextEmbedding
from fastembed import TextEmbedding

from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter


# Constants
PDF_PATH = "./D23569.pdf"
EMBED_MODEL_ID = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
MAX_TOKENS = 750
# NER_MODEL_NAME = "dslim/bert-large-NER" # Generic NER model - example 1
# NER_MODEL_NAME = "lfcc/bert-portuguese-ner" # Portuguese NER model - example 2
NER_MODEL_NAME = "pierreguillou/ner-bert-base-cased-pt-lenerbr"  # Pt. Legal NER model
MIN_ENTITY_CONFIDENCE = 0.80  # Minimum confidence threshold for entity extraction


def convert_pdf_to_document(pdf_path):
    """
    Convert a PDF file to a structured document format.
    """
    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    return result.document


def create_document_chunks(document, embed_model_id, max_tokens):
    """
    Split the document into manageable chunks for processing.
    """
    tokenizer = AutoTokenizer.from_pretrained(embed_model_id)

    chunker = HybridChunker(
        tokenizer=tokenizer,
        max_tokens=max_tokens,
        merge_peers=True,
    )

    chunk_iter = chunker.chunk(dl_doc=document)
    return list(chunk_iter)


def setup_ner_pipeline(model_name):
    """
    Set up a Named Entity Recognition pipeline.
    """
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForTokenClassification.from_pretrained(model_name)

    return pipeline(
        "ner", model=model, tokenizer=tokenizer, aggregation_strategy="first"
    )


def extract_entities_from_chunk(chunk_text, ner_pipeline, min_confidence=0.75):
    """
    Extract named entities from a text chunk with quality filtering.

    Args:
        chunk_text (str): The text to extract entities from
        ner_pipeline: The NER pipeline to use
        min_confidence (float): Minimum confidence threshold

    Returns:
        dict: Dictionary of entity types and their values
    """
    # Limit text size to prevent performance issues
    if len(chunk_text) > 5000:
        chunk_text = chunk_text[:5000]

    # Extract entities using the NER pipeline
    raw_entities = ner_pipeline(chunk_text)

    # Filter entities by confidence and length
    filtered_entities = {}

    for entity in raw_entities:
        # Skip very short tokens (unless they're acronyms)
        if len(entity["word"]) < 2 and not entity["word"].isupper():
            continue

        # Filter by confidence score
        if entity.get("score", 0) < min_confidence:
            continue

        entity_type = entity["entity_group"]

        if entity_type not in filtered_entities:
            filtered_entities[entity_type] = set()

        filtered_entities[entity_type].add(entity["word"])

    # Convert sets to lists for better serialization
    for entity_type in filtered_entities:
        filtered_entities[entity_type] = list(filtered_entities[entity_type])

    return filtered_entities


def enrich_chunks_with_metadata(chunks, ner_pipeline):
    """
    Add metadata to each document chunk, including extracted entities.
    """
    enriched_chunks = []

    for i, chunk in enumerate(chunks):
        # Basic metadata
        metadata = {
            "chunk_id": i,
            "page_numbers": getattr(chunk.meta, "page_numbers", None)
            if hasattr(chunk, "meta")
            else None,
        }

        # Add headings if available
        if hasattr(chunk, "meta") and hasattr(chunk.meta, "headings"):
            metadata["headings"] = chunk.meta.headings

        # Only process substantial chunks (> 20 words)
        if len(chunk.text.split()) > 20:
            try:
                entities = extract_entities_from_chunk(
                    chunk.text, ner_pipeline, MIN_ENTITY_CONFIDENCE
                )
                if entities:
                    metadata["entities"] = entities
            except Exception as e:
                metadata["entities_error"] = str(e)

        enriched_chunks.append({"text": chunk.text, "metadata": metadata})

    return enriched_chunks


def initialize_embedding_models():
    """
    Initialize the three embedding models needed for hybrid search:
    """
    dense_embedding_model = TextEmbedding(
        "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    )
    bm25_embedding_model = Bm25("Qdrant/bm25")
    colbert_embedding_model = LateInteractionTextEmbedding("colbert-ir/colbertv2.0")

    return dense_embedding_model, bm25_embedding_model, colbert_embedding_model


def create_embeddings(chunk_text, dense_model, bm25_model, colbert_model):
    """
    Create the three types of embeddings for a text chunk.
    """
    # Generate embeddings for each model
    dense_embedding = list(dense_model.passage_embed([chunk_text]))[0].tolist()
    sparse_embedding = list(bm25_model.passage_embed([chunk_text]))[0].as_object()
    colbert_embedding = list(colbert_model.passage_embed([chunk_text]))[0].tolist()

    return {
        "dense": dense_embedding,
        "sparse": sparse_embedding,
        "colbertv2.0": colbert_embedding,
    }


def prepare_point(chunk, embedding_models):
    """
    Prepare a single data point for Qdrant ingestion.
    """
    dense_model, bm25_model, colbert_model = embedding_models

    # Extract text from chunk based on your structure
    text = chunk.get("text", "")

    # Create embeddings
    embeddings = create_embeddings(text, dense_model, bm25_model, colbert_model)

    # Prepare payload with metadata from chunk
    payload = {"text": text, "metadata": chunk.get("metadata", {})}

    # Create and return the point
    return PointStruct(
        id=str(uuid.uuid4()),
        vector={
            "dense": embeddings["dense"],
            "sparse": embeddings["sparse"],
            "colbertv2.0": embeddings["colbertv2.0"],
        },
        payload=payload,
    )


def upload_in_batches(
    client: QdrantClient,
    collection_name: str,
    points: List[PointStruct],
    batch_size: int = 10,
):
    """
    Upload points to Qdrant in batches with progress tracking.
    """
    # Calculate number of batches
    n_batches = (len(points) + batch_size - 1) // batch_size

    print(
        f"Uploading {len(points)} points to collection '{collection_name}' in {n_batches} batches..."
    )

    # Process each batch with progress bar
    for i in tqdm(range(0, len(points), batch_size), total=n_batches):
        batch = points[i : i + batch_size]
        client.upload_points(collection_name=collection_name, points=batch)

    print(
        f"Successfully uploaded {len(points)} points to collection '{collection_name}'"
    )


def process_and_upload_chunks(chunks, collection_name):
    """
    Process document chunks and upload them to Qdrant.
    """
    # Load environment variables
    load_dotenv()

    # Initialize client
    client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
    )

    # Initialize embedding models
    embedding_models = initialize_embedding_models()

    # Prepare points
    print("Preparing points with embeddings...")
    points = []
    for chunk in tqdm(chunks):
        point = prepare_point(chunk, embedding_models)
        points.append(point)

    # Upload points in batches
    upload_in_batches(
        client=client,
        collection_name=collection_name,
        points=points,
        batch_size=4,  # Adjust based on your document size and memory constraints
    )

    # Print confirmation with collection info
    collection_info = client.get_collection(collection_name)
    print(
        f"Collection '{collection_name}' now has {collection_info.points_count} points"
    )


# Running
# Convert PDF to document
document = convert_pdf_to_document(PDF_PATH)

# Create document chunks
chunks = create_document_chunks(document, EMBED_MODEL_ID, MAX_TOKENS)
print(f"Document split into {len(chunks)} chunks")

# Set up NER pipeline
ner_pipeline = setup_ner_pipeline(NER_MODEL_NAME)

# Process chunks and extract metadata
enriched_chunks = enrich_chunks_with_metadata(chunks, ner_pipeline)

# Display results
for i, chunk in enumerate(enriched_chunks):
    print(chunk)

# Send data to Qdrant
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
process_and_upload_chunks(enriched_chunks, COLLECTION_NAME)
