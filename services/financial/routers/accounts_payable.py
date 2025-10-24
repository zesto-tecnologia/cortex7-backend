"""
Contas a Pagar router.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import date
from uuid import UUID

from shared.database.connection import get_db
from shared.models.financial import AccountPayable as AccountPayable
from services.financial.schemas.account_payable import (
    AccountPayableCreate,
    AccountPayableUpdate,
    AccountPayableResponse,
)

router = APIRouter()


@router.get("/", response_model=List[AccountPayableResponse])
async def list_accounts_payable(
    company_id: UUID,
    status: Optional[str] = None,
    due_start: Optional[date] = None,
    due_end: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """List accounts payable with filters."""
    query = select(AccountPayable).where(AccountPayable.company_id == company_id)

    if status:
        query = query.where(AccountPayable.status == status)

    if due_start:
        query = query.where(AccountPayable.due_date >= due_start)

    if due_end:
        query = query.where(AccountPayable.due_date <= due_end)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{account_id}", response_model=AccountPayableResponse)
async def get_account_payable(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific account payable."""
    result = await db.execute(
        select(AccountPayable).where(AccountPayable.id == account_id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account payable not found")

    return account


@router.post("/", response_model=AccountPayableResponse)
async def create_account_payable(
    account: AccountPayableCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new account payable."""
    db_account = AccountPayable(**account.dict())
    db.add(db_account)
    await db.commit()
    await db.refresh(db_account)
    return db_account


@router.put("/{account_id}", response_model=AccountPayableResponse)
async def update_account_payable(
    account_id: UUID,
    account_update: AccountPayableUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a account payable."""
    result = await db.execute(
        select(AccountPayable).where(AccountPayable.id == account_id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account payable not found")

    for field, value in account_update.dict(exclude_unset=True).items():
        setattr(account, field, value)

    await db.commit()
    await db.refresh(account)
    return account


@router.delete("/{account_id}")
async def delete_account_payable(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a account payable."""
    result = await db.execute(
        select(AccountPayable).where(AccountPayable.id == account_id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account payable not found")

    await db.delete(account)
    await db.commit()
    return {"message": "Account payable deleted successfully"}