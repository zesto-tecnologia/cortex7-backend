"""
Pydantic schemas for Documents.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


class DocumentoBase(BaseModel):
    """Base schema for Document."""

    empresa_id: UUID
    departamento: str = Field(..., max_length=50)
    tipo: str = Field(..., max_length=50)
    titulo: Optional[str] = Field(None, max_length=255)
    conteudo_original: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    arquivo_url: Optional[str] = Field(None, max_length=500)
    status: str = Field(default="ativo", max_length=20)


class DocumentoCreate(DocumentoBase):
    """Schema for creating a Document."""
    pass


class DocumentoUpdate(BaseModel):
    """Schema for updating a Document."""

    departamento: Optional[str] = Field(None, max_length=50)
    tipo: Optional[str] = Field(None, max_length=50)
    titulo: Optional[str] = Field(None, max_length=255)
    conteudo_original: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    arquivo_url: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, max_length=20)


class DocumentoResponse(DocumentoBase):
    """Schema for Document response."""

    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    has_embedding: bool = Field(default=False)

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to handle embedding field."""
        data = {
            "id": obj.id,
            "empresa_id": obj.empresa_id,
            "departamento": obj.departamento,
            "tipo": obj.tipo,
            "titulo": obj.titulo,
            "conteudo_original": obj.conteudo_original,
            "metadata": obj.metadata,
            "arquivo_url": obj.arquivo_url,
            "status": obj.status,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            "has_embedding": obj.embedding is not None
        }
        return cls(**data)