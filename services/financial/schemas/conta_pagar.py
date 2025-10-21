"""
Pydantic schemas for Contas a Pagar.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


class ContaPagarBase(BaseModel):
    """Base schema for Conta a Pagar."""

    empresa_id: UUID
    fornecedor_id: Optional[UUID] = None
    documento_id: Optional[UUID] = None
    numero_documento: Optional[str] = Field(None, max_length=50)
    descricao: Optional[str] = None
    valor: Decimal = Field(..., decimal_places=2)
    data_vencimento: date
    data_pagamento: Optional[date] = None
    status: str = Field(default="pendente", max_length=20)
    centro_custo: Optional[str] = Field(None, max_length=50)
    categoria: Optional[str] = Field(None, max_length=50)
    meta_data: Optional[Dict[str, Any]] = None
    prioridade: int = Field(default=5, ge=1, le=10)


class ContaPagarCreate(ContaPagarBase):
    """Schema for creating a Conta a Pagar."""
    pass


class ContaPagarUpdate(BaseModel):
    """Schema for updating a Conta a Pagar."""

    fornecedor_id: Optional[UUID] = None
    documento_id: Optional[UUID] = None
    numero_documento: Optional[str] = Field(None, max_length=50)
    descricao: Optional[str] = None
    valor: Optional[Decimal] = Field(None, decimal_places=2)
    data_vencimento: Optional[date] = None
    data_pagamento: Optional[date] = None
    status: Optional[str] = Field(None, max_length=20)
    centro_custo: Optional[str] = Field(None, max_length=50)
    categoria: Optional[str] = Field(None, max_length=50)
    meta_data: Optional[Dict[str, Any]] = None
    prioridade: Optional[int] = Field(None, ge=1, le=10)


class ContaPagarResponse(ContaPagarBase):
    """Schema for Conta a Pagar response."""

    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True