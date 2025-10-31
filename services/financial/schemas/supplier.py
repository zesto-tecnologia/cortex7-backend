"""
Pydantic schemas for Supplieres (Suppliers).
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


class SupplierBase(BaseModel):
    """Base schema for Supplier."""

    company_id: UUID
    company_name: str = Field(..., max_length=255)
    cnpj: str = Field(..., min_length=14, max_length=14)
    category: Optional[str] = Field(None, max_length=50)
    status: str = Field(default="active", max_length=20)
    bank_details: Optional[Dict[str, Any]] = None
    contacts: Optional[List[Dict[str, Any]]] = None
    ratings: Optional[Dict[str, Any]] = None


class SupplierCreate(SupplierBase):
    """Schema for creating a Supplier."""
    pass


class SupplierUpdate(BaseModel):
    """Schema for updating a Supplier."""

    company_name: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=20)
    bank_details: Optional[Dict[str, Any]] = None
    contacts: Optional[List[Dict[str, Any]]] = None
    ratings: Optional[Dict[str, Any]] = None


class SupplierResponse(SupplierBase):
    """Schema for Supplier response."""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True