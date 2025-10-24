"""
Prazos e Alertas (Deadlines and Alerts) router.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import date, timedelta
from uuid import UUID

from shared.database.connection import get_db
from shared.models.legal import Contract, LegalProcess as Lawsuit

router = APIRouter()


@router.get("/all/{company_id}")
async def get_all_deadlines(
    company_id: UUID,
    days_limit: int = 90,
    db: AsyncSession = Depends(get_db),
):
    """Get all deadlines and important dates."""
    deadline_date = date.today() + timedelta(days=days_limit)
    deadlines = []

    # Contract deadlines
    contratos_query = select(Contract).where(
        and_(
            Contract.company_id == company_id,
            Contract.status == "vigente",
            Contract.end_date != None,
            Contract.end_date <= deadline_date
        )
    )
    contratos_result = await db.execute(contratos_query)
    contracts = contratos_result.scalars().all()

    for contract in contracts:
        dias_restantes = (contract.end_date - date.today()).days

        deadlines.append({
            "type": "contrato_vencimento",
            "entidade_id": contract.id,
            "description": f"Vencimento contract: {contract.opposing_party}",
            "date": contract.end_date,
            "dias_restantes": dias_restantes,
            "prioridade": "alta" if dias_restantes <= 15 else "media",
            "renovacao_automatica": contract.renovacao_automatica
        })

        # Contract critical deadlines
        if contract.prazos_importantes:
            for deadline in contract.prazos_importantes:
                prazo_data = date.fromisoformat(deadline["date"])
                if prazo_data <= deadline_date:
                    dias_restantes = (prazo_data - date.today()).days
                    deadlines.append({
                        "type": "contrato_prazo_critico",
                        "entidade_id": contract.id,
                        "description": deadline["description"],
                        "date": prazo_data,
                        "dias_restantes": dias_restantes,
                        "prioridade": "alta" if dias_restantes <= 7 else "media",
                        "notificado": deadline.get("notificado", False)
                    })

    # Legal process deadlines
    processos_query = select(Lawsuit).where(
        and_(
            Lawsuit.company_id == company_id,
            Lawsuit.status == "andamento",
            Lawsuit.next_action != None,
            Lawsuit.next_action <= deadline_date
        )
    )
    processos_result = await db.execute(processos_query)
    lawsuits = processos_result.scalars().all()

    for lawsuit in lawsuits:
        dias_restantes = (lawsuit.next_action - date.today()).days

        deadlines.append({
            "type": "processo_acao",
            "entidade_id": lawsuit.id,
            "description": lawsuit.next_action_description or f"Ação lawsuit: {lawsuit.lawsuit_number}",
            "date": lawsuit.next_action,
            "dias_restantes": dias_restantes,
            "prioridade": "critica" if dias_restantes <= 3 else "alta" if dias_restantes <= 7 else "media",
            "risco_processo": lawsuit.risco
        })

    # Sort by date
    deadlines.sort(key=lambda x: x["date"])

    return deadlines


@router.get("/critical/{company_id}")
async def get_prazos_criticos(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get critical deadlines (next 7 days)."""
    prazos_todos = await get_all_deadlines(company_id, days_limit=7, db=db)

    # Filter only high priority
    prazos_criticos = [
        p for p in prazos_todos
        if p["prioridade"] in ["critica", "alta"]
    ]

    return {
        "total_criticos": len(prazos_criticos),
        "deadlines": prazos_criticos
    }


@router.get("/calendar/{company_id}")
async def get_calendario_prazos(
    company_id: UUID,
    ano: int = 2025,
    mes: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get deadline calendar."""
    import calendar

    # Define date range
    if mes:
        start_date = date(ano, mes, 1)
        end_date = date(ano, mes, calendar.monthrange(ano, mes)[1])
    else:
        start_date = date(ano, 1, 1)
        end_date = date(ano, 12, 31)

    # Get all deadlines for the period
    prazos_todos = await get_all_deadlines(company_id, days_limit=365, db=db)

    # Filter by date range
    calendario = {}
    for deadline in prazos_todos:
        if start_date <= deadline["date"] <= end_date:
            data_str = str(deadline["date"])
            if data_str not in calendario:
                calendario[data_str] = []
            calendario[data_str].append(deadline)

    return calendario


@router.post("/marcar-notificado/{company_id}")
async def marcar_prazo_notificado(
    company_id: UUID,
    tipo_entidade: str,  # "contract" or "lawsuit"
    entidade_id: UUID,
    deadline_description: str,
    db: AsyncSession = Depends(get_db),
):
    """Mark a deadline as notified."""
    if tipo_entidade == "contract":
        result = await db.execute(
            select(Contract).where(
                and_(
                    Contract.id == entidade_id,
                    Contract.company_id == company_id
                )
            )
        )
        contract = result.scalar_one_or_none()

        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")

        if contract.prazos_importantes:
            for deadline in contract.prazos_importantes:
                if deadline["description"] == deadline_description:
                    deadline["notificado"] = True
                    break

        await db.commit()
        return {"message": "Deadline marked as notified"}

    else:
        raise HTTPException(status_code=400, detail="Invalid entity type")