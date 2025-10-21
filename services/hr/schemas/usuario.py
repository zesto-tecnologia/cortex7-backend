"""
Pydantic schemas for Usuários (Users).
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class UsuarioBase(BaseModel):
    """Base schema for User."""

    empresa_id: UUID
    departamento_id: Optional[UUID] = None
    nome: str = Field(..., max_length=255)
    email: EmailStr
    cargo: Optional[str] = Field(None, max_length=100)
    alcadas: Optional[Dict[str, float]] = None
    status: str = Field(default="ativo", max_length=20)


class UsuarioCreate(UsuarioBase):
    """Schema for creating a User."""
    pass


class UsuarioUpdate(BaseModel):
    """Schema for updating a User."""

    departamento_id: Optional[UUID] = None
    nome: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    cargo: Optional[str] = Field(None, max_length=100)
    alcadas: Optional[Dict[str, float]] = None
    status: Optional[str] = Field(None, max_length=20)


class UsuarioResponse(UsuarioBase):
    """Schema for User response."""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True