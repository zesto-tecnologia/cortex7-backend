"""
Pydantic schemas for Contas a Pagar.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


class AccountPayableBase(BaseModel):
    """Base schema for Account Payable."""

    company_id: UUID
    supplier_id: Optional[UUID] = None
    document_id: Optional[UUID] = None
    document_number: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    value: Decimal = Field(..., decimal_places=2)
    due_date: date
    payment_date: Optional[date] = None
    status: str = Field(default="pendente", max_length=20)
    cost_center: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=50)
    metadata: Optional[Dict[str, Any]] = None
    prioridade: int = Field(default=5, ge=1, le=10)


class AccountPayableCreate(AccountPayableBase):
    """Schema for creating a Account Payable."""
    pass


class AccountPayableUpdate(BaseModel):
    """Schema for updating a Account Payable."""

    supplier_id: Optional[UUID] = None
    document_id: Optional[UUID] = None
    document_number: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    value: Optional[Decimal] = Field(None, decimal_places=2)
    due_date: Optional[date] = None
    payment_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=20)
    cost_center: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=50)
    metadata: Optional[Dict[str, Any]] = None
    prioridade: Optional[int] = Field(None, ge=1, le=10)


class AccountPayableResponse(AccountPayableBase):
    """Schema for Account Payable response."""

    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True