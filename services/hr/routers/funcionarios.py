"""
Funcionários (Employees) router.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from datetime import date
from uuid import UUID

from shared.database.connection import get_db
from shared.models.rh import Funcionario
from services.hr.schemas.funcionario import (
    FuncionarioCreate,
    FuncionarioUpdate,
    FuncionarioResponse,
    FuncionarioWithContracts,
)

router = APIRouter()


@router.get("/", response_model=List[FuncionarioResponse])
async def list_funcionarios(
    empresa_id: UUID,
    departamento_id: Optional[UUID] = None,
    status: Optional[str] = "ativo",
    cargo: Optional[str] = None,
    tipo_contrato: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """List employees with filters."""
    query = select(Funcionario).where(
        Funcionario.empresa_id == empresa_id,
        Funcionario.status == status
    )

    if departamento_id:
        query = query.where(Funcionario.departamento_id == departamento_id)

    if cargo:
        query = query.where(Funcionario.cargo.ilike(f"%{cargo}%"))

    if tipo_contrato:
        query = query.where(Funcionario.tipo_contrato == tipo_contrato)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/search")
async def search_funcionarios(
    empresa_id: UUID,
    q: str,
    db: AsyncSession = Depends(get_db),
):
    """Search employees by name or CPF."""
    query = select(Funcionario).where(
        Funcionario.empresa_id == empresa_id,
        or_(
            Funcionario.cpf.contains(q),
            Funcionario.cargo.ilike(f"%{q}%")
        )
    )

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{funcionario_id}", response_model=FuncionarioWithContracts)
async def get_funcionario(
    funcionario_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific employee with contracts."""
    from sqlalchemy.orm import selectinload

    query = select(Funcionario).options(
        selectinload(Funcionario.contratos_trabalho),
        selectinload(Funcionario.usuario),
        selectinload(Funcionario.departamento)
    ).where(Funcionario.id == funcionario_id)

    result = await db.execute(query)
    funcionario = result.scalar_one_or_none()

    if not funcionario:
        raise HTTPException(status_code=404, detail="Employee not found")

    return funcionario


@router.post("/", response_model=FuncionarioResponse)
async def create_funcionario(
    funcionario: FuncionarioCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new employee."""
    # Check if CPF already exists
    existing = await db.execute(
        select(Funcionario).where(Funcionario.cpf == funcionario.cpf)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="CPF already registered")

    db_funcionario = Funcionario(**funcionario.dict())
    db.add(db_funcionario)
    await db.commit()
    await db.refresh(db_funcionario)
    return db_funcionario


@router.put("/{funcionario_id}", response_model=FuncionarioResponse)
async def update_funcionario(
    funcionario_id: UUID,
    funcionario_update: FuncionarioUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an employee."""
    result = await db.execute(
        select(Funcionario).where(Funcionario.id == funcionario_id)
    )
    funcionario = result.scalar_one_or_none()

    if not funcionario:
        raise HTTPException(status_code=404, detail="Employee not found")

    for field, value in funcionario_update.dict(exclude_unset=True).items():
        setattr(funcionario, field, value)

    await db.commit()
    await db.refresh(funcionario)
    return funcionario


@router.post("/{funcionario_id}/demissao")
async def registrar_demissao(
    funcionario_id: UUID,
    data_demissao: date,
    db: AsyncSession = Depends(get_db),
):
    """Register employee termination."""
    result = await db.execute(
        select(Funcionario).where(Funcionario.id == funcionario_id)
    )
    funcionario = result.scalar_one_or_none()

    if not funcionario:
        raise HTTPException(status_code=404, detail="Employee not found")

    funcionario.data_demissao = data_demissao
    funcionario.status = "inativo"

    await db.commit()

    return {"message": "Termination registered successfully"}


@router.get("/{funcionario_id}/ferias-disponiveis")
async def get_ferias_disponiveis(
    funcionario_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get available vacation days for an employee."""
    result = await db.execute(
        select(Funcionario).where(Funcionario.id == funcionario_id)
    )
    funcionario = result.scalar_one_or_none()

    if not funcionario:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Calculate vacation days based on employment time
    from datetime import datetime

    if funcionario.data_admissao:
        months_employed = (
            (datetime.now().date() - funcionario.data_admissao).days / 30
        )
        vacation_periods = int(months_employed / 12)
        available_days = vacation_periods * 30  # 30 days per year in Brazil

        # Subtract used vacation days from ferias JSON field
        used_days = 0
        if funcionario.ferias:
            for periodo in funcionario.ferias.get("historico", []):
                used_days += periodo.get("dias", 0)

        return {
            "funcionario_id": funcionario_id,
            "months_employed": int(months_employed),
            "vacation_periods": vacation_periods,
            "total_earned_days": available_days,
            "used_days": used_days,
            "available_days": available_days - used_days
        }

    return {"available_days": 0}