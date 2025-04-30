from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Configuration
    api_title: str = "RAG API"
    api_description: str = "RAG API with Hybrid Search"
    api_version: str = "0.1.0"

    # Qdrant Configuration
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    collection_name: str = "documents"
    qdrant_timeout: float = 60.0
    prefetch_limit: int = 25

    # Model Configuration
    dense_model_name: str = (
        "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    )
    bm25_model_name: str = "Qdrant/bm25"
    late_interaction_model_name: str = "colbert-ir/colbertv2.0"

    model_config = {"env_file": ".env", "extra": "allow"}
