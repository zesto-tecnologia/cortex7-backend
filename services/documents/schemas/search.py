"""
Pydantic schemas for Search operations.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID


class SearchQuery(BaseModel):
    """Schema for semantic search query."""

    empresa_id: UUID
    text: str = Field(..., min_length=1, max_length=5000)
    departamento: Optional[str] = None
    tipo: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)
    similarity_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)


class SimilaritySearchQuery(BaseModel):
    """Schema for finding similar documents."""

    empresa_id: UUID
    document_id: UUID
    limit: int = Field(default=5, ge=1, le=50)


class SearchResult(BaseModel):
    """Schema for search result."""

    id: UUID
    titulo: Optional[str]
    departamento: str
    tipo: str
    conteudo_preview: Optional[str]
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    metadata: Dict[str, Any]
    arquivo_url: Optional[str]


class MetadataSearchQuery(BaseModel):
    """Schema for metadata search."""

    empresa_id: UUID
    filters: Dict[str, Any]
    limit: int = Field(default=100, ge=1, le=500)