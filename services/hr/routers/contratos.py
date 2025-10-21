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
from shared.models.rh import ContratoTrabalho
from services.hr.schemas.contrato import (
    ContratoTrabalhoCreate,
    ContratoTrabalhoUpdate,
    ContratoTrabalhoResponse,
)

router = APIRouter()


@router.get("/funcionario/{funcionario_id}", response_model=List[ContratoTrabalhoResponse])
async def list_contratos_funcionario(
    funcionario_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all contracts for an employee."""
    query = select(ContratoTrabalho).where(
        ContratoTrabalho.funcionario_id == funcionario_id
    ).order_by(ContratoTrabalho.data_inicio.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{contrato_id}", response_model=ContratoTrabalhoResponse)
async def get_contrato(
    contrato_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific employment contract."""
    result = await db.execute(
        select(ContratoTrabalho).where(ContratoTrabalho.id == contrato_id)
    )
    contrato = result.scalar_one_or_none()

    if not contrato:
        raise HTTPException(status_code=404, detail="Contract not found")

    return contrato


@router.post("/", response_model=ContratoTrabalhoResponse)
async def create_contrato(
    contrato: ContratoTrabalhoCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new employment contract."""
    db_contrato = ContratoTrabalho(**contrato.dict())
    db.add(db_contrato)
    await db.commit()
    await db.refresh(db_contrato)
    return db_contrato


@router.put("/{contrato_id}", response_model=ContratoTrabalhoResponse)
async def update_contrato(
    contrato_id: UUID,
    contrato_update: ContratoTrabalhoUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an employment contract."""
    result = await db.execute(
        select(ContratoTrabalho).where(ContratoTrabalho.id == contrato_id)
    )
    contrato = result.scalar_one_or_none()

    if not contrato:
        raise HTTPException(status_code=404, detail="Contract not found")

    for field, value in contrato_update.dict(exclude_unset=True).items():
        setattr(contrato, field, value)

    await db.commit()
    await db.refresh(contrato)
    return contrato


@router.post("/{contrato_id}/assinar")
async def assinar_contrato(
    contrato_id: UUID,
    assinatura_funcionario: bool = False,
    assinatura_empresa: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Sign an employment contract."""
    result = await db.execute(
        select(ContratoTrabalho).where(ContratoTrabalho.id == contrato_id)
    )
    contrato = result.scalar_one_or_none()

    if not contrato:
        raise HTTPException(status_code=404, detail="Contract not found")

    from datetime import datetime

    if assinatura_funcionario:
        contrato.assinatura_funcionario_data = datetime.now()

    if assinatura_empresa:
        contrato.assinatura_empresa_data = datetime.now()

    # Mark as signed if both parties have signed
    if contrato.assinatura_funcionario_data and contrato.assinatura_empresa_data:
        contrato.assinado = True

    await db.commit()
    await db.refresh(contrato)

    return {
        "message": "Contract signed successfully",
        "assinado": contrato.assinado,
        "assinatura_funcionario": contrato.assinatura_funcionario_data is not None,
        "assinatura_empresa": contrato.assinatura_empresa_data is not None
    }