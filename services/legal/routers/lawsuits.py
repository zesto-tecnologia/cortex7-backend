"""
Processos Jurídicos (Legal Processes) router.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import date
from uuid import UUID

from shared.database.connection import get_db
from shared.models.legal import Lawsuit
from services.legal.schemas.lawsuit import (
    LawsuitCreate,
    LawsuitUpdate,
    LawsuitResponse,
    LawsuitHistory,
)

router = APIRouter()


@router.get("/", response_model=List[LawsuitResponse])
async def list_lawsuits(
    company_id: UUID,
    lawsuit_type: Optional[str] = None,
    status: Optional[str] = None,
    risk: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """List lawsuits with filters."""
    query = select(Lawsuit).where(
        Lawsuit.company_id == company_id
    )

    if lawsuit_type:
        query = query.where(Lawsuit.lawsuit_type == lawsuit_type)

    if status:
        query = query.where(Lawsuit.status == status)

    if risk:
        query = query.where(Lawsuit.risk == risk)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/next-actions")
async def get_next_actions(
    company_id: UUID,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
):
    """Get lawsuits with upcoming actions."""
    deadline_date = date.today().replace(day=date.today().day + days)

    query = select(Lawsuit).where(
        and_(
            Lawsuit.company_id == company_id,
            Lawsuit.status == "active",
            Lawsuit.next_action != None,
            Lawsuit.next_action <= deadline_date
        )
    ).order_by(Lawsuit.next_action)

    result = await db.execute(query)
    lawsuits = result.scalars().all()

    return [
        {
            "id": lawsuit.id,
            "case_number": lawsuit.case_number,
            "lawsuit_type": lawsuit.lawsuit_type,
            "counterparty": lawsuit.counterparty,
            "cause_amount": lawsuit.cause_amount,
            "status": lawsuit.status,
            "risk": lawsuit.risk,
            "court": lawsuit.court,
            "responsible_attorney": lawsuit.responsible_attorney,
            "history": lawsuit.history,
            "next_action": lawsuit.next_action,
            "next_action_description": lawsuit.next_action_description,
            "document_ids": lawsuit.document_ids
        }
        for lawsuit in lawsuits
    ]


@router.get("/{lawsuit_id}", response_model=LawsuitResponse)
async def get_lawsuit(
    lawsuit_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific lawsuit."""
    result = await db.execute(
        select(Lawsuit).where(Lawsuit.id == lawsuit_id)
    )
    lawsuit = result.scalar_one_or_none()

    if not lawsuit:
        raise HTTPException(status_code=404, detail="Lawsuit not found")

    return lawsuit


@router.post("/", response_model=LawsuitResponse)
async def create_lawsuit(
    lawsuit: LawsuitCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new lawsuit."""
    # Check if process number already exists
    if lawsuit.case_number:
        existing = await db.execute(
            select(Lawsuit).where(
                Lawsuit.case_number == lawsuit.case_number
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Case number already exists"
            )

    db_lawsuit = Lawsuit(**lawsuit.dict())
    db.add(db_lawsuit)
    await db.commit()
    await db.refresh(db_lawsuit)
    return db_lawsuit


@router.put("/{lawsuit_id}", response_model=LawsuitResponse)
async def update_lawsuit(
    lawsuit_id: UUID,
    lawsuit_update: LawsuitUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a lawsuit."""
    result = await db.execute(
        select(Lawsuit).where(Lawsuit.id == lawsuit_id)
    )
    lawsuit = result.scalar_one_or_none()

    if not lawsuit:
        raise HTTPException(status_code=404, detail="Lawsuit not found")

    for field, value in lawsuit_update.dict(exclude_unset=True).items():
        setattr(lawsuit, field, value)

    await db.commit()
    await db.refresh(lawsuit)
    return lawsuit


@router.post("/{lawsuit_id}/add-history")
async def add_history(
    lawsuit_id: UUID,
    history: List[LawsuitHistory],
    db: AsyncSession = Depends(get_db),
):
    """Add history entry to a lawsuit."""
    result = await db.execute(
        select(Lawsuit).where(Lawsuit.id == lawsuit_id)
    )
    lawsuit = result.scalar_one_or_none()

    if not lawsuit:
        raise HTTPException(status_code=404, detail="Lawsuit not found")

    if not lawsuit.history:
        lawsuit.history = []

    lawsuit.history.append({
        "date": str(history.date),
        "event": history.event,
        "description": history.description,
        "responsible": history.responsible
    })

    await db.commit()

    return {"message": "History entry added successfully"}


@router.get("/report/risks")
async def get_risk_report(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get risk report for all lawsuits."""
    query = select(Lawsuit).where(
        Lawsuit.company_id == company_id,
        Lawsuit.status == "active"
    )

    result = await db.execute(query)
    lawsuits = result.scalars().all()

    # Aggregate by risk level
    risks = {
        "low": {"quantity": 0, "total_value": 0},
        "medium": {"quantity": 0, "total_value": 0},
        "high": {"quantity": 0, "total_value": 0}
    }

    for lawsuit in lawsuits:
        if lawsuit.risk in risks:
            risks[lawsuit.risk]["quantity"] += 1
            if lawsuit.cause_amount:
                risks[lawsuit.risk]["total_value"] += float(lawsuit.cause_amount)

    # Aggregate by type
    types = {}
    for lawsuit in lawsuits:
        if lawsuit.lawsuit_type not in types:
            types[lawsuit.lawsuit_type] = {"quantity": 0, "total_value": 0}

        types[lawsuit.lawsuit_type]["quantity"] += 1
        if lawsuit.cause_amount:
            types[lawsuit.lawsuit_type]["total_value"] += float(lawsuit.cause_amount)

    return {
        "company_id": company_id,
        "total_lawsuits": len(lawsuits),
        "risks": risks,
        "types": types,
        "total_cause_amount": sum(
            float(lawsuit.cause_amount) for lawsuit in lawsuits if lawsuit.cause_amount
        )
    }