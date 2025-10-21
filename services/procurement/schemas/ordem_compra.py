"""
Pydantic schemas for Ordens de Compra (Purchase Orders).
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


class ItemOrdemCompra(BaseModel):
    """Schema for purchase order item."""

    descricao: str = Field(..., min_length=1, max_length=500)
    quantidade: int = Field(..., ge=1)
    valor_unitario: float = Field(..., gt=0)
    unidade: Optional[str] = Field(None, max_length=10)  # UN, KG, L, etc.
    observacoes: Optional[str] = None


class OrdemCompraBase(BaseModel):
    """Base schema for Purchase Order."""

    empresa_id: UUID
    solicitante_id: UUID
    fornecedor_id: UUID
    centro_custo: Optional[str] = Field(None, max_length=50)
    data_entrega_prevista: Optional[date] = None
    metadata: Optional[Dict[str, Any]] = None


class OrdemCompraCreate(OrdemCompraBase):
    """Schema for creating a Purchase Order."""

    itens: List[ItemOrdemCompra] = Field(..., min_items=1)
    status: str = Field(default="rascunho", max_length=30)

    @validator('itens')
    def validate_itens(cls, v):
        if not v:
            raise ValueError('Order must have at least one item')
        return v


class OrdemCompraUpdate(BaseModel):
    """Schema for updating a Purchase Order."""

    fornecedor_id: Optional[UUID] = None
    itens: Optional[List[ItemOrdemCompra]] = None
    centro_custo: Optional[str] = Field(None, max_length=50)
    data_entrega_prevista: Optional[date] = None
    metadata: Optional[Dict[str, Any]] = None


class OrdemCompraResponse(OrdemCompraBase):
    """Schema for Purchase Order response."""

    id: UUID
    numero: str
    valor_total: Decimal
    status: str
    itens: List[Dict[str, Any]]
    aprovadores: Optional[List[Dict[str, Any]]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OrdemCompraWithAprovacoes(OrdemCompraResponse):
    """Purchase Order with approval details."""

    solicitante: Optional["UsuarioResponse"] = None
    fornecedor: Optional["FornecedorResponse"] = None

    class Config:
        from_attributes = True


# Import after class definition to avoid circular imports
from services.financial.schemas.fornecedor import FornecedorResponse
from services.hr.schemas.usuario import UsuarioResponse

OrdemCompraWithAprovacoes.model_rebuild()