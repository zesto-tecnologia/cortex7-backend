"""
Pydantic schemas for Embeddings.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class EmbeddingRequest(BaseModel):
    """Schema for embedding generation request."""

    text: str = Field(..., min_length=1, max_length=50000)
    model: Optional[str] = Field(default="text-embedding-ada-002")


class BatchEmbeddingRequest(BaseModel):
    """Schema for batch embedding generation."""

    texts: List[str] = Field(..., min_items=1, max_items=100)
    model: Optional[str] = Field(default="text-embedding-ada-002")


class EmbeddingResponse(BaseModel):
    """Schema for embedding response."""

    text: str
    embedding: List[float]
    model: str
    cached: bool = False