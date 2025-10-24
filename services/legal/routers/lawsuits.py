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
from shared.models.legal import LegalProcess as Lawsuit
from services.legal.schemas.lawsuit import (
    LawsuitCreate,
    LawsuitUpdate,
    LawsuitResponse,
    LawsuitHistory,
)

router = APIRouter()


@router.get("/", response_model=List[LawsuitResponse])
async def list_processos(
    company_id: UUID,
    type: Optional[str] = None,
    status: Optional[str] = None,
    risco: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """List legal processes with filters."""
    query = select(Lawsuit).where(
        Lawsuit.company_id == company_id
    )

    if type:
        query = query.where(Lawsuit.type == type)

    if status:
        query = query.where(Lawsuit.status == status)

    if risco:
        query = query.where(Lawsuit.risco == risco)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/proximas-acoes")
async def get_proximas_acoes(
    company_id: UUID,
    dias: int = 30,
    db: AsyncSession = Depends(get_db),
):
    """Get processes with upcoming actions."""
    deadline_date = date.today().replace(day=date.today().day + dias)

    query = select(Lawsuit).where(
        and_(
            Lawsuit.company_id == company_id,
            Lawsuit.status == "andamento",
            Lawsuit.next_action != None,
            Lawsuit.next_action <= deadline_date
        )
    ).order_by(Lawsuit.next_action)

    result = await db.execute(query)
    lawsuits = result.scalars().all()

    return [
        {
            "id": p.id,
            "lawsuit_number": p.lawsuit_number,
            "type": p.type,
            "opposing_party": p.opposing_party,
            "next_action": p.next_action,
            "next_action_description": p.next_action_description,
            "dias_restantes": (p.next_action - date.today()).days,
            "risco": p.risco,
            "advogado_responsavel": p.advogado_responsavel
        }
        for p in lawsuits
    ]


@router.get("/{processo_id}", response_model=LawsuitResponse)
async def get_processo(
    processo_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific legal process."""
    result = await db.execute(
        select(Lawsuit).where(Lawsuit.id == processo_id)
    )
    lawsuit = result.scalar_one_or_none()

    if not lawsuit:
        raise HTTPException(status_code=404, detail="Process not found")

    return lawsuit


@router.post("/", response_model=LawsuitResponse)
async def create_processo(
    lawsuit: LawsuitCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new legal process."""
    # Check if process number already exists
    if lawsuit.lawsuit_number:
        existing = await db.execute(
            select(Lawsuit).where(
                Lawsuit.lawsuit_number == lawsuit.lawsuit_number
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Process number already exists"
            )

    db_processo = Lawsuit(**lawsuit.dict())
    db.add(db_processo)
    await db.commit()
    await db.refresh(db_processo)
    return db_processo


@router.put("/{processo_id}", response_model=LawsuitResponse)
async def update_processo(
    processo_id: UUID,
    processo_update: LawsuitUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a legal process."""
    result = await db.execute(
        select(Lawsuit).where(Lawsuit.id == processo_id)
    )
    lawsuit = result.scalar_one_or_none()

    if not lawsuit:
        raise HTTPException(status_code=404, detail="Process not found")

    for field, value in processo_update.dict(exclude_unset=True).items():
        setattr(lawsuit, field, value)

    await db.commit()
    await db.refresh(lawsuit)
    return lawsuit


@router.post("/{processo_id}/adicionar-historico")
async def adicionar_historico(
    processo_id: UUID,
    historico: LawsuitHistory,
    db: AsyncSession = Depends(get_db),
):
    """Add history entry to a legal process."""
    result = await db.execute(
        select(Lawsuit).where(Lawsuit.id == processo_id)
    )
    lawsuit = result.scalar_one_or_none()

    if not lawsuit:
        raise HTTPException(status_code=404, detail="Process not found")

    if not lawsuit.historico:
        lawsuit.historico = []

    lawsuit.historico.append({
        "date": str(historico.date),
        "event": historico.event,
        "description": historico.description,
        "responsible": historico.responsible
    })

    await db.commit()

    return {"message": "History entry added successfully"}


@router.get("/report/riscos")
async def get_relatorio_riscos(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get risk report for all processes."""
    query = select(Lawsuit).where(
        Lawsuit.company_id == company_id,
        Lawsuit.status == "andamento"
    )

    result = await db.execute(query)
    lawsuits = result.scalars().all()

    # Aggregate by risk level
    riscos = {
        "baixo": {"quantity": 0, "total_value": 0},
        "medio": {"quantity": 0, "total_value": 0},
        "alto": {"quantity": 0, "total_value": 0}
    }

    for lawsuit in lawsuits:
        if lawsuit.risco in riscos:
            riscos[lawsuit.risco]["quantity"] += 1
            if lawsuit.lawsuit_value:
                riscos[lawsuit.risco]["total_value"] += float(lawsuit.lawsuit_value)

    # Aggregate by type
    tipos = {}
    for lawsuit in lawsuits:
        if lawsuit.type not in tipos:
            tipos[lawsuit.type] = {"quantity": 0, "total_value": 0}

        tipos[lawsuit.type]["quantity"] += 1
        if lawsuit.lawsuit_value:
            tipos[lawsuit.type]["total_value"] += float(lawsuit.lawsuit_value)

    return {
        "company_id": company_id,
        "total_processos": len(lawsuits),
        "riscos": riscos,
        "tipos": tipos,
        "total_value_at_risk": sum(
            float(p.lawsuit_value) for p in lawsuits if p.lawsuit_value
        )
    }