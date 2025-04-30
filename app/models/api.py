from pydantic import BaseModel
from typing import List, Optional
from app.models.embeddings import Document


class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5


class SearchResponse(BaseModel):
    results: List[Document]
