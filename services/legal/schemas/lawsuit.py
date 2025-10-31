"""
Pydantic schemas for Lawsuits.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


class LawsuitBase(BaseModel):
    """Base schema for Lawsuit."""

    company_id: UUID
    case_number: Optional[str] = Field(None, max_length=50)
    lawsuit_type: Optional[str] = Field(None, max_length=50)
    parte_contraria: Optional[str] = Field(None, max_length=255)
    cause_amount: Optional[Decimal] = Field(None, decimal_places=2)
    status: Optional[str] = Field(None, max_length=30)
    risk: Optional[str] = Field(None, max_length=20)
    tribunal: Optional[str] = Field(None, max_length=100)
    responsible_attorney: Optional[str] = Field(None, max_length=255)
    history: Optional[List[Dict[str, Any]]] = None
    next_action: Optional[date] = None
    next_action_description: Optional[str] = None
    documentos_ids: Optional[List[UUID]] = None


class LawsuitCreate(LawsuitBase):
    """Schema for creating a Lawsuit."""
    pass


class LawsuitUpdate(BaseModel):
    """Schema for updating a Lawsuit."""

    case_number: Optional[str] = Field(None, max_length=50)
    lawsuit_type: Optional[str] = Field(None, max_length=50)
    counterparty: Optional[str] = Field(None, max_length=255)
    cause_amount: Optional[Decimal] = Field(None, decimal_places=2)
    status: Optional[str] = Field(None, max_length=30)
    risk: Optional[str] = Field(None, max_length=20)
    tribunal: Optional[str] = Field(None, max_length=100)
    responsible_attorney: Optional[str] = Field(None, max_length=255)
    history: Optional[List[Dict[str, Any]]] = None
    next_action: Optional[date] = None
    next_action_description: Optional[str] = None
    document_ids: Optional[List[UUID]] = None


class LawsuitResponse(LawsuitBase):
    """Schema for Lawsuit response."""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class LawsuitHistory(BaseModel):
    """Schema for lawsuit history entry."""

    date: date
    event: str = Field(..., max_length=100)
    description: str
    responsible: Optional[str] = Field(None, max_length=255)