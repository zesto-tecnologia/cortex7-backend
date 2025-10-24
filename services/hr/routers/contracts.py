"""
Contratos de Trabalho (Employment Contracts) router.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from datetime import datetime

from shared.database.connection import get_db
from shared.models.hr import EmploymentContract
from services.hr.schemas.contract import (
    EmploymentContractCreate,
    EmploymentContractUpdate,
    EmploymentContractResponse,
)

router = APIRouter()


@router.get("/employee/{employee_id}", response_model=List[EmploymentContractResponse])
async def list_contracts_for_employee(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all contracts for an employee."""
    query = select(EmploymentContract).where(
        EmploymentContract.employee_id == employee_id
    ).order_by(EmploymentContract.start_date.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{contract_id}", response_model=EmploymentContractResponse)
async def get_contract(
    contract_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific employment contract."""
    result = await db.execute(
        select(EmploymentContract).where(EmploymentContract.id == contract_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    return contract


@router.post("/", response_model=EmploymentContractResponse)
async def create_contract(
    contract: EmploymentContractCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new employment contract."""
    db_contract = EmploymentContract(**contract.dict())
    db.add(db_contract)
    await db.commit()
    await db.refresh(db_contract)
    return db_contract


@router.put("/{contract_id}", response_model=EmploymentContractResponse)
async def update_contract(
    contract_id: UUID,
    contract_update: EmploymentContractUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an employment contract."""
    result = await db.execute(
        select(EmploymentContract).where(EmploymentContract.id == contract_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    for field, value in contract_update.dict(exclude_unset=True).items():
        setattr(contract, field, value)

    await db.commit()
    await db.refresh(contract)
    return contract


@router.post("/{contract_id}/sign")
async def sign_contract(
    contract_id: UUID,
    employee_signature: bool = False,
    company_signature: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Sign an employment contract."""
    result = await db.execute(
        select(EmploymentContract).where(EmploymentContract.id == contract_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")


    if employee_signature:
        contract.employee_signature_date = datetime.now()

    if company_signature:
        contract.company_signature_date = datetime.now()

    # Mark as signed if both parties have signed
    if contract.employee_signature_date and contract.company_signature_date:
        contract.signed = True

    await db.commit()
    await db.refresh(contract)

    return {
        "message": "Contract signed successfully",
        "signed": contract.signed,
        "employee_signature": contract.employee_signature_date is not None,
        "company_signature": contract.company_signature_date is not None
    }