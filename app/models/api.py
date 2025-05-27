from pydantic import BaseModel
from typing import List, Optional
from app.models.embeddings import Document


class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5


class SearchResponse(BaseModel):
    results: List[Document]


class OpenAIRequest(BaseModel):
    query: str
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_output_tokens: Optional[int] = None
    limit: Optional[int] = 5


class OpenAIResponse(BaseModel):
    answer: str
    source_documents: List[Document]
