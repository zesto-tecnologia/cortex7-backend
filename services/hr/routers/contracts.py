"""
Contratos de Trabalho (Employment Contracts) router.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from datetime import date

from shared.database.connection import get_db
from shared.models.hr import EmploymentContract
from services.hr.schemas.contract import (
    EmploymentContractCreate,
    EmploymentContractUpdate,
    EmploymentContractResponse,
)

router = APIRouter()


@router.get("/employee/{employee_id}", response_model=List[EmploymentContractResponse])
async def list_contratos_funcionario(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all contracts for an employee."""
    query = select(EmploymentContract).where(
        EmploymentContract.employee_id == employee_id
    ).order_by(EmploymentContract.start_date.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{contrato_id}", response_model=EmploymentContractResponse)
async def get_contrato(
    contrato_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific employment contract."""
    result = await db.execute(
        select(EmploymentContract).where(EmploymentContract.id == contrato_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    return contract


@router.post("/", response_model=EmploymentContractResponse)
async def create_contrato(
    contract: EmploymentContractCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new employment contract."""
    db_contrato = EmploymentContract(**contract.dict())
    db.add(db_contrato)
    await db.commit()
    await db.refresh(db_contrato)
    return db_contrato


@router.put("/{contrato_id}", response_model=EmploymentContractResponse)
async def update_contrato(
    contrato_id: UUID,
    contrato_update: EmploymentContractUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an employment contract."""
    result = await db.execute(
        select(EmploymentContract).where(EmploymentContract.id == contrato_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    for field, value in contrato_update.dict(exclude_unset=True).items():
        setattr(contract, field, value)

    await db.commit()
    await db.refresh(contract)
    return contract


@router.post("/{contrato_id}/assinar")
async def assinar_contrato(
    contrato_id: UUID,
    assinatura_funcionario: bool = False,
    assinatura_empresa: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Sign an employment contract."""
    result = await db.execute(
        select(EmploymentContract).where(EmploymentContract.id == contrato_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    from datetime import datetime

    if assinatura_funcionario:
        contract.assinatura_funcionario_data = datetime.now()

    if assinatura_empresa:
        contract.assinatura_empresa_data = datetime.now()

    # Mark as signed if both parties have signed
    if contract.assinatura_funcionario_data and contract.assinatura_empresa_data:
        contract.assinado = True

    await db.commit()
    await db.refresh(contract)

    return {
        "message": "Contract signed successfully",
        "assinado": contract.assinado,
        "assinatura_funcionario": contract.assinatura_funcionario_data is not None,
        "assinatura_empresa": contract.assinatura_empresa_data is not None
    }