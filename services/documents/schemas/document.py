"""
Pydantic schemas for Documents.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


class DocumentBase(BaseModel):
    """Base schema for Document."""

    company_id: UUID
    department: str = Field(..., max_length=50)
    type: str = Field(..., max_length=50)
    title: Optional[str] = Field(None, max_length=255)
    original_content: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    file_url: Optional[str] = Field(None, max_length=500)
    status: str = Field(default="ativo", max_length=20)


class DocumentCreate(DocumentBase):
    """Schema for creating a Document."""
    pass


class DocumentUpdate(BaseModel):
    """Schema for updating a Document."""

    department: Optional[str] = Field(None, max_length=50)
    type: Optional[str] = Field(None, max_length=50)
    title: Optional[str] = Field(None, max_length=255)
    original_content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    file_url: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, max_length=20)


class DocumentResponse(DocumentBase):
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
        date = {
            "id": obj.id,
            "company_id": obj.company_id,
            "department": obj.department,
            "type": obj.type,
            "title": obj.title,
            "original_content": obj.original_content,
            "metadata": obj.metadata,
            "file_url": obj.file_url,
            "status": obj.status,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            "has_embedding": obj.embedding is not None
        }
        return cls(**date)