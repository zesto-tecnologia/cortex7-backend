"""
Pydantic schemas for Processos Jurídicos (Legal Processes).
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


class ProcessoJuridicoBase(BaseModel):
    """Base schema for Legal Process."""

    empresa_id: UUID
    numero_processo: Optional[str] = Field(None, max_length=50)
    tipo: Optional[str] = Field(None, max_length=50)
    parte_contraria: Optional[str] = Field(None, max_length=255)
    valor_causa: Optional[Decimal] = Field(None, decimal_places=2)
    status: Optional[str] = Field(None, max_length=30)
    risco: Optional[str] = Field(None, max_length=20)
    tribunal: Optional[str] = Field(None, max_length=100)
    advogado_responsavel: Optional[str] = Field(None, max_length=255)
    historico: Optional[List[Dict[str, Any]]] = None
    proxima_acao: Optional[date] = None
    proxima_acao_descricao: Optional[str] = None
    documentos_ids: Optional[List[UUID]] = None


class ProcessoJuridicoCreate(ProcessoJuridicoBase):
    """Schema for creating a Legal Process."""
    pass


class ProcessoJuridicoUpdate(BaseModel):
    """Schema for updating a Legal Process."""

    numero_processo: Optional[str] = Field(None, max_length=50)
    tipo: Optional[str] = Field(None, max_length=50)
    parte_contraria: Optional[str] = Field(None, max_length=255)
    valor_causa: Optional[Decimal] = Field(None, decimal_places=2)
    status: Optional[str] = Field(None, max_length=30)
    risco: Optional[str] = Field(None, max_length=20)
    tribunal: Optional[str] = Field(None, max_length=100)
    advogado_responsavel: Optional[str] = Field(None, max_length=255)
    historico: Optional[List[Dict[str, Any]]] = None
    proxima_acao: Optional[date] = None
    proxima_acao_descricao: Optional[str] = None
    documentos_ids: Optional[List[UUID]] = None


class ProcessoJuridicoResponse(ProcessoJuridicoBase):
    """Schema for Legal Process response."""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ProcessoHistorico(BaseModel):
    """Schema for process history entry."""

    data: date
    evento: str = Field(..., max_length=100)
    descricao: str
    responsavel: Optional[str] = Field(None, max_length=255)