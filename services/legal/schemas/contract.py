"""
Pydantic schemas for Contracts (Legal Contracts).
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


class ContractBase(BaseModel):
    """Base schema for Contract."""

    company_id: UUID
    document_id: Optional[UUID] = None
    type: str = Field(..., max_length=50)
    counterparty: str = Field(..., max_length=255)
    counterparty_tax_id: Optional[str] = Field(None, max_length=14)
    subject: str
    amount: Optional[Decimal] = Field(None, decimal_places=2)
    start_date: date
    end_date: Optional[date] = None
    auto_renewal: bool = Field(default=False)
    status: str = Field(default="active", max_length=20)
    critical_clauses: Optional[Dict[str, Any]] = None
    important_dates: Optional[List[Dict[str, Any]]] = None
    responsible_id: Optional[UUID] = None
    meta_data: Optional[Dict[str, Any]] = None


class ContractCreate(ContractBase):
    """Schema for creating a Contract."""
    pass


class ContractUpdate(BaseModel):
    """Schema for updating a Contract."""

    document_id: Optional[UUID] = None
    type: Optional[str] = Field(None, max_length=50)
    counterparty: Optional[str] = Field(None, max_length=255)
    counterparty_tax_id: Optional[str] = Field(None, max_length=14)
    subject: Optional[str] = None
    amount: Optional[Decimal] = Field(None, decimal_places=2)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    auto_renewal: Optional[bool] = None
    status: Optional[str] = Field(None, max_length=20)
    critical_clauses: Optional[Dict[str, Any]] = None
    important_dates: Optional[List[Dict[str, Any]]] = None
    responsible_id: Optional[UUID] = None
    meta_data: Optional[Dict[str, Any]] = None


class ContractResponse(ContractBase):
    """Schema for Contract response."""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ContractWithAlerts(ContractResponse):
    """Contract with alerts."""

    alerts: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True