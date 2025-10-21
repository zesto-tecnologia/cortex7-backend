"""
Pydantic schemas for Contratos (Legal Contracts).
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


class ContratoBase(BaseModel):
    """Base schema for Contract."""

    empresa_id: UUID
    documento_id: Optional[UUID] = None
    tipo: str = Field(..., max_length=50)
    parte_contraria: str = Field(..., max_length=255)
    cnpj_cpf_contraparte: Optional[str] = Field(None, max_length=14)
    objeto: str
    valor: Optional[Decimal] = Field(None, decimal_places=2)
    data_inicio: date
    data_fim: Optional[date] = None
    renovacao_automatica: bool = Field(default=False)
    status: str = Field(default="vigente", max_length=20)
    clausulas_criticas: Optional[Dict[str, Any]] = None
    prazos_importantes: Optional[List[Dict[str, Any]]] = None
    responsavel_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None


class ContratoCreate(ContratoBase):
    """Schema for creating a Contract."""
    pass


class ContratoUpdate(BaseModel):
    """Schema for updating a Contract."""

    documento_id: Optional[UUID] = None
    tipo: Optional[str] = Field(None, max_length=50)
    parte_contraria: Optional[str] = Field(None, max_length=255)
    cnpj_cpf_contraparte: Optional[str] = Field(None, max_length=14)
    objeto: Optional[str] = None
    valor: Optional[Decimal] = Field(None, decimal_places=2)
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    renovacao_automatica: Optional[bool] = None
    status: Optional[str] = Field(None, max_length=20)
    clausulas_criticas: Optional[Dict[str, Any]] = None
    prazos_importantes: Optional[List[Dict[str, Any]]] = None
    responsavel_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None


class ContratoResponse(ContratoBase):
    """Schema for Contract response."""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ContratoWithAlertas(ContratoResponse):
    """Contract with alerts."""

    alertas: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True