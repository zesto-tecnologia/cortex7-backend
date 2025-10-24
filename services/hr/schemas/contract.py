"""
Pydantic schemas for Contracts de Trabalho (Employment Contracts).
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import date, datetime
from uuid import UUID


class EmploymentContractBase(BaseModel):
    """Base schema for Employment Contract."""

    funcionario_id: UUID
    document_id: Optional[UUID] = None
    type: str = Field(..., max_length=20)  # admissao, alteracao, rescisao
    data_inicio: date
    data_fim: Optional[date] = None
    conteudo: Optional[str] = None
    clausulas_especiais: Optional[Dict[str, Any]] = None
    assinado: bool = Field(default=False)
    assinatura_funcionario_data: Optional[datetime] = None
    assinatura_empresa_data: Optional[datetime] = None


class EmploymentContractCreate(EmploymentContractBase):
    """Schema for creating an Employment Contract."""
    pass


class EmploymentContractUpdate(BaseModel):
    """Schema for updating an Employment Contract."""

    document_id: Optional[UUID] = None
    type: Optional[str] = Field(None, max_length=20)
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    conteudo: Optional[str] = None
    clausulas_especiais: Optional[Dict[str, Any]] = None
    assinado: Optional[bool] = None


class EmploymentContractResponse(EmploymentContractBase):
    """Schema for Employment Contract response."""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True