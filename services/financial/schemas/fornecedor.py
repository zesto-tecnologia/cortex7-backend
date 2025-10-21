"""
Pydantic schemas for Fornecedores (Suppliers).
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


class FornecedorBase(BaseModel):
    """Base schema for Supplier."""

    empresa_id: UUID
    razao_social: str = Field(..., max_length=255)
    cnpj: str = Field(..., min_length=14, max_length=14)
    categoria: Optional[str] = Field(None, max_length=50)
    status: str = Field(default="ativo", max_length=20)
    dados_bancarios: Optional[Dict[str, Any]] = None
    contatos: Optional[List[Dict[str, Any]]] = None
    avaliacoes: Optional[Dict[str, Any]] = None


class FornecedorCreate(FornecedorBase):
    """Schema for creating a Supplier."""
    pass


class FornecedorUpdate(BaseModel):
    """Schema for updating a Supplier."""

    razao_social: Optional[str] = Field(None, max_length=255)
    categoria: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=20)
    dados_bancarios: Optional[Dict[str, Any]] = None
    contatos: Optional[List[Dict[str, Any]]] = None
    avaliacoes: Optional[Dict[str, Any]] = None


class FornecedorResponse(FornecedorBase):
    """Schema for Supplier response."""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True