"""
Pydantic schemas for Contracts de Trabalho (Employment Contracts).
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import date, datetime
from uuid import UUID


class EmploymentContractBase(BaseModel):
    """Base schema for Employment Contract."""

    employee_id: UUID
    document_id: Optional[UUID] = None
    type: str = Field(..., max_length=20)  # hire, amendment, termination
    start_date: date
    end_date: Optional[date] = None
    content: Optional[str] = None
    special_clauses: Optional[Dict[str, Any]] = None
    signed: bool = Field(default=False)
    employee_signature_date: Optional[datetime] = None
    company_signature_date: Optional[datetime] = None


class EmploymentContractCreate(EmploymentContractBase):
    """Schema for creating an employment contract."""
    pass


class EmploymentContractUpdate(BaseModel):
    """Schema for updating an employment contract."""

    document_id: Optional[UUID] = None
    type: Optional[str] = Field(None, max_length=20)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    content: Optional[str] = None
    special_clauses: Optional[Dict[str, Any]] = None
    signed: Optional[bool] = None
    employee_signature_date: Optional[datetime] = None
    company_signature_date: Optional[datetime] = None


class EmploymentContractResponse(EmploymentContractBase):
    """Schema for Employment Contract response."""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True