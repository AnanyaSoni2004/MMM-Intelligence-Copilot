from pydantic import BaseModel, Field
from typing import Optional

class RetrievedChunk(BaseModel):
    chunk_id: str
    document_title: str
    content: str
    relevance_score: float = Field(..., ge=0, le=1)
    page_or_section: Optional[str] = None

class RAGResponse(BaseModel):
    query: str
    answer: str = Field(..., description="Generated answer grounded in retrieved chunks")
    retrieved_chunks: list[RetrievedChunk]
    citations: list[str] = Field(..., description="Inline citation references")
    confidence: float = Field(..., ge=0, le=1)
    beyond_context: bool = Field(False, description="True if query cannot be answered from retrieved context")
    grounded: bool = Field(True)
