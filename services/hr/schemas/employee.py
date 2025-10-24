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
    usuario_id: Optional[UUID] = None
    cpf: str = Field(..., min_length=11, max_length=11)
    data_nascimento: Optional[date] = None
    data_admissao: date
    data_demissao: Optional[date] = None
    cargo: str = Field(..., max_length=100)
    departamento_id: Optional[UUID] = None
    salario: Optional[Decimal] = Field(None, decimal_places=2)
    tipo_contrato: Optional[str] = Field(None, max_length=20)
    regime_trabalho: Optional[str] = Field(None, max_length=20)
    dados_pessoais: Optional[Dict[str, Any]] = None
    beneficios: Optional[Dict[str, Any]] = None
    documentos: Optional[Dict[str, Any]] = None
    ferias: Optional[Dict[str, Any]] = None
    status: str = Field(default="ativo", max_length=20)


class EmployeeCreate(EmployeeBase):
    """Schema for creating an Employee."""
    pass


class EmployeeUpdate(BaseModel):
    """Schema for updating an Employee."""

    usuario_id: Optional[UUID] = None
    data_nascimento: Optional[date] = None
    data_demissao: Optional[date] = None
    cargo: Optional[str] = Field(None, max_length=100)
    departamento_id: Optional[UUID] = None
    salario: Optional[Decimal] = Field(None, decimal_places=2)
    tipo_contrato: Optional[str] = Field(None, max_length=20)
    regime_trabalho: Optional[str] = Field(None, max_length=20)
    dados_pessoais: Optional[Dict[str, Any]] = None
    beneficios: Optional[Dict[str, Any]] = None
    documentos: Optional[Dict[str, Any]] = None
    ferias: Optional[Dict[str, Any]] = None
    status: Optional[str] = Field(None, max_length=20)


class EmployeeResponse(EmployeeBase):
    """Schema for Employee response."""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class EmployeeWithContracts(EmployeeResponse):
    """Employee with contracts."""

    contratos_trabalho: List["EmploymentContractResponse"] = []

    class Config:
        from_attributes = True


# Import after class definition to avoid circular imports
from services.hr.schemas.contract import EmploymentContractResponse

EmployeeWithContracts.model_rebuild()