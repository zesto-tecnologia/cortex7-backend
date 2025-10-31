"""
Contratos (Legal Contracts) router.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import date, timedelta
from uuid import UUID

from shared.database.connection import get_db
from shared.models.legal import Contract
from services.legal.schemas.contract import (
    ContractCreate,
    ContractUpdate,
    ContractResponse,
    ContractWithAlerts,
)

router = APIRouter()


@router.get("/", response_model=List[ContractResponse])
async def list_contracts(
    company_id: UUID,
    type: Optional[str] = None,
    status: Optional[str] = None,
    expiring_in_days: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """List contracts with filters."""
    query = select(Contract).where(Contract.company_id == company_id)

    if type:
        query = query.where(Contract.type == type)

    if status:
        query = query.where(Contract.status == status)

    if expiring_in_days:
        deadline_date = date.today() + timedelta(days=expiring_in_days)
        query = query.where(
            and_(
                Contract.end_date != None,
                Contract.end_date <= deadline_date
            )
        )

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/expiration")
async def get_contracts_expiration(
    company_id: UUID,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
):
    """Get contracts expiring within specified days."""
    deadline_date = date.today() + timedelta(days=days)

    query = select(Contract).where(
        and_(
            Contract.company_id == company_id,
            Contract.status == "active",
            Contract.end_date != None,
            Contract.end_date <= deadline_date
        )
    ).order_by(Contract.end_date)

    result = await db.execute(query)
    contracts = result.scalars().all()

    return [
        {
            "id": c.id,
            "type": c.type,
            "counterparty": c.counterparty,
            "counterparty_tax_id": c.counterparty_tax_id,
            "subject": c.subject,
            "amount": float(c.amount) if c.amount else None,
            "start_date": c.start_date,
            "end_date": c.end_date,
            "days_to_expiration": (c.end_date - date.today()).days,
            "auto_renewal": c.auto_renewal,
            "value": float(c.amount) if c.amount else None
        }
        for c in contracts
    ]


@router.get("/{contract_id}", response_model=ContractWithAlerts)
async def get_contract(
    contract_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific contract with alerts."""
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Calculate alerts
    alerts = []

    if contract.end_date:
        days_to_expiration = (contract.end_date - date.today()).days

        if days_to_expiration <= 30:
            alerts.append({
                "type": "expiration_soon",
                "message": f"Contract expires in {days_to_expiration} days",
                "priority": "high" if days_to_expiration <= 7 else "medium"
            })

    if contract.important_dates:
        for deadline in contract.important_dates:
            deadline_date = date.fromisoformat(deadline["date"])
            days_to_deadline = (deadline_date - date.today()).days

            if days_to_deadline <= 15 and not deadline.get("notified"):
                alerts.append({
                    "type": "important_date",
                    "message": deadline["description"],
                    "days_remaining": days_to_deadline,
                    "priority": "high" if days_to_deadline <= 3 else "medium"
                })

    response = ContractWithAlerts(**contract.__dict__)
    response.alerts = alerts
    return response


@router.post("/", response_model=ContractResponse)
async def create_contract(
    contract: ContractCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new contract."""
    db_contract = Contract(**contract.dict())
    db.add(db_contract)
    await db.commit()
    await db.refresh(db_contract)
    return db_contract


@router.put("/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: UUID,
    contract_update: ContractUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a contract."""
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    for field, value in contract_update.dict(exclude_unset=True).items():
        setattr(contract, field, value)

    await db.commit()
    await db.refresh(contract)
    return contract


@router.post("/{contract_id}/renew")
async def renew_contract(
    contract_id: UUID,
    new_end_date: date,
    db: AsyncSession = Depends(get_db),
):
    """Renew a contract."""
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Update contract end date
    contract.end_date = new_end_date
    contract.status = "active"

    # Add renewal to metadata
    if not contract.metadata:
        contract.metadata = {}

    if "renewals" not in contract.metadata:
        contract.metadata["renewals"] = []

    contract.metadata["renewals"].append({
        "renewal_date": str(date.today()),
        "new_end_date": str(new_end_date)
    })

    await db.commit()

    return {"message": "Contract renewed successfully", "new_end_date": new_end_date}


@router.post("/{contract_id}/terminate")
async def terminate_contract(
    contract_id: UUID,
    termination_date: date,
    reason: str,
    db: AsyncSession = Depends(get_db),
):
    """Terminate a contract."""
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    contract.status = "terminated"
    contract.end_date = termination_date

    if not contract.metadata:
        contract.metadata = {}

    contract.metadata["termination"] = {
        "date": str(termination_date),
        "reason": reason,
        "registered_at": str(date.today())
    }

    await db.commit()

    return {"message": "Contract terminated successfully"}