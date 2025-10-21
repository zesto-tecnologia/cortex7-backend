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
from shared.models.financeiro import ContaPagar
from services.financial.schemas.conta_pagar import (
    ContaPagarCreate,
    ContaPagarUpdate,
    ContaPagarResponse,
)

router = APIRouter()


@router.get("/", response_model=List[ContaPagarResponse])
async def list_contas_pagar(
    empresa_id: UUID,
    status: Optional[str] = None,
    vencimento_inicio: Optional[date] = None,
    vencimento_fim: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """List contas a pagar with filters."""
    query = select(ContaPagar).where(ContaPagar.empresa_id == empresa_id)

    if status:
        query = query.where(ContaPagar.status == status)

    if vencimento_inicio:
        query = query.where(ContaPagar.data_vencimento >= vencimento_inicio)

    if vencimento_fim:
        query = query.where(ContaPagar.data_vencimento <= vencimento_fim)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{conta_id}", response_model=ContaPagarResponse)
async def get_conta_pagar(
    conta_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific conta a pagar."""
    result = await db.execute(
        select(ContaPagar).where(ContaPagar.id == conta_id)
    )
    conta = result.scalar_one_or_none()

    if not conta:
        raise HTTPException(status_code=404, detail="Conta a pagar not found")

    return conta


@router.post("/", response_model=ContaPagarResponse)
async def create_conta_pagar(
    conta: ContaPagarCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new conta a pagar."""
    db_conta = ContaPagar(**conta.dict())
    db.add(db_conta)
    await db.commit()
    await db.refresh(db_conta)
    return db_conta


@router.put("/{conta_id}", response_model=ContaPagarResponse)
async def update_conta_pagar(
    conta_id: UUID,
    conta_update: ContaPagarUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a conta a pagar."""
    result = await db.execute(
        select(ContaPagar).where(ContaPagar.id == conta_id)
    )
    conta = result.scalar_one_or_none()

    if not conta:
        raise HTTPException(status_code=404, detail="Conta a pagar not found")

    for field, value in conta_update.dict(exclude_unset=True).items():
        setattr(conta, field, value)

    await db.commit()
    await db.refresh(conta)
    return conta


@router.delete("/{conta_id}")
async def delete_conta_pagar(
    conta_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a conta a pagar."""
    result = await db.execute(
        select(ContaPagar).where(ContaPagar.id == conta_id)
    )
    conta = result.scalar_one_or_none()

    if not conta:
        raise HTTPException(status_code=404, detail="Conta a pagar not found")

    await db.delete(conta)
    await db.commit()
    return {"message": "Conta a pagar deleted successfully"}