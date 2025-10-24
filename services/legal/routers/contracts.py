"""
Contratos (Legal Contracts) router.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
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
async def list_contratos(
    company_id: UUID,
    type: Optional[str] = None,
    status: Optional[str] = None,
    vencendo_em_dias: Optional[int] = None,
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

    if vencendo_em_dias:
        deadline_date = date.today() + timedelta(days=vencendo_em_dias)
        query = query.where(
            and_(
                Contract.end_date != None,
                Contract.end_date <= deadline_date
            )
        )

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/vencimentos")
async def get_contratos_vencimento(
    company_id: UUID,
    dias: int = 30,
    db: AsyncSession = Depends(get_db),
):
    """Get contracts expiring within specified days."""
    deadline_date = date.today() + timedelta(days=dias)

    query = select(Contract).where(
        and_(
            Contract.company_id == company_id,
            Contract.status == "vigente",
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
            "opposing_party": c.opposing_party,
            "objeto": c.objeto,
            "end_date": c.end_date,
            "days_to_expiration": (c.end_date - date.today()).days,
            "renovacao_automatica": c.renovacao_automatica,
            "value": float(c.value) if c.value else None
        }
        for c in contracts
    ]


@router.get("/{contrato_id}", response_model=ContractWithAlerts)
async def get_contrato(
    contrato_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific contract with alerts."""
    result = await db.execute(
        select(Contract).where(Contract.id == contrato_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Calculate alerts
    alertas = []

    if contract.end_date:
        days_to_expiration = (contract.end_date - date.today()).days

        if days_to_expiration <= 30:
            alertas.append({
                "type": "vencimento_proximo",
                "message": f"Contract vence em {days_to_expiration} dias",
                "prioridade": "alta" if days_to_expiration <= 7 else "media"
            })

    if contract.prazos_importantes:
        for deadline in contract.prazos_importantes:
            prazo_data = date.fromisoformat(deadline["date"])
            dias_para_prazo = (prazo_data - date.today()).days

            if dias_para_prazo <= 15 and not deadline.get("notificado"):
                alertas.append({
                    "type": "prazo_importante",
                    "message": deadline["description"],
                    "dias_restantes": dias_para_prazo,
                    "prioridade": "alta" if dias_para_prazo <= 3 else "media"
                })

    response = ContractWithAlerts(**contract.__dict__)
    response.alertas = alertas
    return response


@router.post("/", response_model=ContractResponse)
async def create_contrato(
    contract: ContractCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new contract."""
    db_contrato = Contract(**contract.dict())
    db.add(db_contrato)
    await db.commit()
    await db.refresh(db_contrato)
    return db_contrato


@router.put("/{contrato_id}", response_model=ContractResponse)
async def update_contrato(
    contrato_id: UUID,
    contrato_update: ContractUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a contract."""
    result = await db.execute(
        select(Contract).where(Contract.id == contrato_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    for field, value in contrato_update.dict(exclude_unset=True).items():
        setattr(contract, field, value)

    await db.commit()
    await db.refresh(contract)
    return contract


@router.post("/{contrato_id}/renovar")
async def renovar_contrato(
    contrato_id: UUID,
    novo_fim: date,
    db: AsyncSession = Depends(get_db),
):
    """Renew a contract."""
    result = await db.execute(
        select(Contract).where(Contract.id == contrato_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Update contract end date
    contract.end_date = novo_fim
    contract.status = "vigente"

    # Add renewal to metadata
    if not contract.metadata:
        contract.metadata = {}

    if "renovacoes" not in contract.metadata:
        contract.metadata["renovacoes"] = []

    contract.metadata["renovacoes"].append({
        "renewal_date": str(date.today()),
        "new_end_date": str(novo_fim)
    })

    await db.commit()

    return {"message": "Contract renewed successfully", "new_end_date": novo_fim}


@router.post("/{contrato_id}/rescindir")
async def rescindir_contrato(
    contrato_id: UUID,
    termination_date: date,
    motivo: str,
    db: AsyncSession = Depends(get_db),
):
    """Terminate a contract."""
    result = await db.execute(
        select(Contract).where(Contract.id == contrato_id)
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    contract.status = "rescindido"
    contract.end_date = termination_date

    if not contract.metadata:
        contract.metadata = {}

    contract.metadata["rescisao"] = {
        "date": str(termination_date),
        "motivo": motivo,
        "registrado_em": str(date.today())
    }

    await db.commit()

    return {"message": "Contract terminated successfully"}