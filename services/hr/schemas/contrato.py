"""
Pydantic schemas for Contratos de Trabalho (Employment Contracts).
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import date, datetime
from uuid import UUID


class ContratoTrabalhoBase(BaseModel):
    """Base schema for Employment Contract."""

    funcionario_id: UUID
    documento_id: Optional[UUID] = None
    tipo: str = Field(..., max_length=20)  # admissao, alteracao, rescisao
    data_inicio: date
    data_fim: Optional[date] = None
    conteudo: Optional[str] = None
    clausulas_especiais: Optional[Dict[str, Any]] = None
    assinado: bool = Field(default=False)
    assinatura_funcionario_data: Optional[datetime] = None
    assinatura_empresa_data: Optional[datetime] = None


class ContratoTrabalhoCreate(ContratoTrabalhoBase):
    """Schema for creating an Employment Contract."""
    pass


class ContratoTrabalhoUpdate(BaseModel):
    """Schema for updating an Employment Contract."""

    documento_id: Optional[UUID] = None
    tipo: Optional[str] = Field(None, max_length=20)
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    conteudo: Optional[str] = None
    clausulas_especiais: Optional[Dict[str, Any]] = None
    assinado: Optional[bool] = None


class ContratoTrabalhoResponse(ContratoTrabalhoBase):
    """Schema for Employment Contract response."""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True