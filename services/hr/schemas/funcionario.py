"""
Pydantic schemas for Funcionários (Employees).
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


class FuncionarioBase(BaseModel):
    """Base schema for Employee."""

    empresa_id: UUID
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


class FuncionarioCreate(FuncionarioBase):
    """Schema for creating an Employee."""
    pass


class FuncionarioUpdate(BaseModel):
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


class FuncionarioResponse(FuncionarioBase):
    """Schema for Employee response."""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class FuncionarioWithContracts(FuncionarioResponse):
    """Employee with contracts."""

    contratos_trabalho: List["ContratoTrabalhoResponse"] = []

    class Config:
        from_attributes = True


# Import after class definition to avoid circular imports
from services.hr.schemas.contrato import ContratoTrabalhoResponse

FuncionarioWithContracts.model_rebuild()