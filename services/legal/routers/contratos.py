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
from shared.models.juridico import Contrato
from services.legal.schemas.contrato import (
    ContratoCreate,
    ContratoUpdate,
    ContratoResponse,
    ContratoWithAlertas,
)

router = APIRouter()


@router.get("/", response_model=List[ContratoResponse])
async def list_contratos(
    empresa_id: UUID,
    tipo: Optional[str] = None,
    status: Optional[str] = None,
    vencendo_em_dias: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """List contracts with filters."""
    query = select(Contrato).where(Contrato.empresa_id == empresa_id)

    if tipo:
        query = query.where(Contrato.tipo == tipo)

    if status:
        query = query.where(Contrato.status == status)

    if vencendo_em_dias:
        data_limite = date.today() + timedelta(days=vencendo_em_dias)
        query = query.where(
            and_(
                Contrato.data_fim != None,
                Contrato.data_fim <= data_limite
            )
        )

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/vencimentos")
async def get_contratos_vencimento(
    empresa_id: UUID,
    dias: int = 30,
    db: AsyncSession = Depends(get_db),
):
    """Get contracts expiring within specified days."""
    data_limite = date.today() + timedelta(days=dias)

    query = select(Contrato).where(
        and_(
            Contrato.empresa_id == empresa_id,
            Contrato.status == "vigente",
            Contrato.data_fim != None,
            Contrato.data_fim <= data_limite
        )
    ).order_by(Contrato.data_fim)

    result = await db.execute(query)
    contratos = result.scalars().all()

    return [
        {
            "id": c.id,
            "tipo": c.tipo,
            "parte_contraria": c.parte_contraria,
            "objeto": c.objeto,
            "data_fim": c.data_fim,
            "dias_para_vencimento": (c.data_fim - date.today()).days,
            "renovacao_automatica": c.renovacao_automatica,
            "valor": float(c.valor) if c.valor else None
        }
        for c in contratos
    ]


@router.get("/{contrato_id}", response_model=ContratoWithAlertas)
async def get_contrato(
    contrato_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific contract with alerts."""
    result = await db.execute(
        select(Contrato).where(Contrato.id == contrato_id)
    )
    contrato = result.scalar_one_or_none()

    if not contrato:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Calculate alerts
    alertas = []

    if contrato.data_fim:
        dias_para_vencimento = (contrato.data_fim - date.today()).days

        if dias_para_vencimento <= 30:
            alertas.append({
                "tipo": "vencimento_proximo",
                "mensagem": f"Contrato vence em {dias_para_vencimento} dias",
                "prioridade": "alta" if dias_para_vencimento <= 7 else "media"
            })

    if contrato.prazos_importantes:
        for prazo in contrato.prazos_importantes:
            prazo_data = date.fromisoformat(prazo["data"])
            dias_para_prazo = (prazo_data - date.today()).days

            if dias_para_prazo <= 15 and not prazo.get("notificado"):
                alertas.append({
                    "tipo": "prazo_importante",
                    "mensagem": prazo["descricao"],
                    "dias_restantes": dias_para_prazo,
                    "prioridade": "alta" if dias_para_prazo <= 3 else "media"
                })

    response = ContratoWithAlertas(**contrato.__dict__)
    response.alertas = alertas
    return response


@router.post("/", response_model=ContratoResponse)
async def create_contrato(
    contrato: ContratoCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new contract."""
    db_contrato = Contrato(**contrato.dict())
    db.add(db_contrato)
    await db.commit()
    await db.refresh(db_contrato)
    return db_contrato


@router.put("/{contrato_id}", response_model=ContratoResponse)
async def update_contrato(
    contrato_id: UUID,
    contrato_update: ContratoUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a contract."""
    result = await db.execute(
        select(Contrato).where(Contrato.id == contrato_id)
    )
    contrato = result.scalar_one_or_none()

    if not contrato:
        raise HTTPException(status_code=404, detail="Contract not found")

    for field, value in contrato_update.dict(exclude_unset=True).items():
        setattr(contrato, field, value)

    await db.commit()
    await db.refresh(contrato)
    return contrato


@router.post("/{contrato_id}/renovar")
async def renovar_contrato(
    contrato_id: UUID,
    novo_fim: date,
    db: AsyncSession = Depends(get_db),
):
    """Renew a contract."""
    result = await db.execute(
        select(Contrato).where(Contrato.id == contrato_id)
    )
    contrato = result.scalar_one_or_none()

    if not contrato:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Update contract end date
    contrato.data_fim = novo_fim
    contrato.status = "vigente"

    # Add renewal to metadata
    if not contrato.metadata:
        contrato.metadata = {}

    if "renovacoes" not in contrato.metadata:
        contrato.metadata["renovacoes"] = []

    contrato.metadata["renovacoes"].append({
        "data_renovacao": str(date.today()),
        "nova_data_fim": str(novo_fim)
    })

    await db.commit()

    return {"message": "Contract renewed successfully", "nova_data_fim": novo_fim}


@router.post("/{contrato_id}/rescindir")
async def rescindir_contrato(
    contrato_id: UUID,
    data_rescisao: date,
    motivo: str,
    db: AsyncSession = Depends(get_db),
):
    """Terminate a contract."""
    result = await db.execute(
        select(Contrato).where(Contrato.id == contrato_id)
    )
    contrato = result.scalar_one_or_none()

    if not contrato:
        raise HTTPException(status_code=404, detail="Contract not found")

    contrato.status = "rescindido"
    contrato.data_fim = data_rescisao

    if not contrato.metadata:
        contrato.metadata = {}

    contrato.metadata["rescisao"] = {
        "data": str(data_rescisao),
        "motivo": motivo,
        "registrado_em": str(date.today())
    }

    await db.commit()

    return {"message": "Contract terminated successfully"}