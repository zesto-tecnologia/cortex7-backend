"""
Pydantic schemas for Processos Jurídicos (Legal Processes).
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


class LawsuitBase(BaseModel):
    """Base schema for Legal Process."""

    company_id: UUID
    case_number: Optional[str] = Field(None, max_length=50)
    type: Optional[str] = Field(None, max_length=50)
    parte_contraria: Optional[str] = Field(None, max_length=255)
    valor_causa: Optional[Decimal] = Field(None, decimal_places=2)
    status: Optional[str] = Field(None, max_length=30)
    risco: Optional[str] = Field(None, max_length=20)
    tribunal: Optional[str] = Field(None, max_length=100)
    advogado_responsavel: Optional[str] = Field(None, max_length=255)
    historico: Optional[List[Dict[str, Any]]] = None
    proxima_acao: Optional[date] = None
    next_action_description: Optional[str] = None
    documentos_ids: Optional[List[UUID]] = None


class LawsuitCreate(LawsuitBase):
    """Schema for creating a Legal Process."""
    pass


class LawsuitUpdate(BaseModel):
    """Schema for updating a Legal Process."""

    case_number: Optional[str] = Field(None, max_length=50)
    type: Optional[str] = Field(None, max_length=50)
    parte_contraria: Optional[str] = Field(None, max_length=255)
    valor_causa: Optional[Decimal] = Field(None, decimal_places=2)
    status: Optional[str] = Field(None, max_length=30)
    risco: Optional[str] = Field(None, max_length=20)
    tribunal: Optional[str] = Field(None, max_length=100)
    advogado_responsavel: Optional[str] = Field(None, max_length=255)
    historico: Optional[List[Dict[str, Any]]] = None
    proxima_acao: Optional[date] = None
    next_action_description: Optional[str] = None
    documentos_ids: Optional[List[UUID]] = None


class LawsuitResponse(LawsuitBase):
    """Schema for Legal Process response."""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class LawsuitHistory(BaseModel):
    """Schema for process history entry."""

    date: date
    event: str = Field(..., max_length=100)
    description: str
    responsible: Optional[str] = Field(None, max_length=255)