"""
Pydantic schemas for Funcionários (Employees).
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


class EmployeeBase(BaseModel):
    """Base schema for Employee."""

    company_id: UUID
    user_id: Optional[UUID] = None
    cpf: str = Field(..., min_length=11, max_length=11)
    birth_date: Optional[date] = None
    hire_date: date
    termination_date: Optional[date] = None
    position: str = Field(..., max_length=100)
    department_id: Optional[UUID] = None
    salary: Optional[Decimal] = Field(None, decimal_places=2)
    contract_type: Optional[str] = Field(None, max_length=20)
    work_mode: Optional[str] = Field(None, max_length=20)
    personal_data: Optional[Dict[str, Any]] = None
    benefits: Optional[Dict[str, Any]] = None
    documents: Optional[Dict[str, Any]] = None
    vacations: Optional[Dict[str, Any]] = None
    status: str = Field(default="active", max_length=20)


class EmployeeCreate(EmployeeBase):
    """Schema for creating an Employee."""
    pass


class EmployeeUpdate(BaseModel):
    """Schema for updating an Employee."""

    user_id: Optional[UUID] = None
    birth_date: Optional[date] = None
    termination_date: Optional[date] = None
    position: Optional[str] = Field(None, max_length=100)
    department_id: Optional[UUID] = None
    salary: Optional[Decimal] = Field(None, decimal_places=2)
    contract_type: Optional[str] = Field(None, max_length=20)
    work_mode: Optional[str] = Field(None, max_length=20)
    personal_data: Optional[Dict[str, Any]] = None
    benefits: Optional[Dict[str, Any]] = None
    documents: Optional[Dict[str, Any]] = None
    vacations: Optional[Dict[str, Any]] = None
    status: Optional[str] = Field(None, max_length=20)


class EmployeeResponse(EmployeeBase):
    """Schema for Employee response."""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class EmployeeWithContracts(EmployeeResponse):
    """Employee with contracts."""

    contracts: List["EmploymentContractResponse"] = []

    class Config:
        from_attributes = True


# Import after class definition to avoid circular imports
from services.hr.schemas.contract import EmploymentContractResponse

EmployeeWithContracts.model_rebuild()