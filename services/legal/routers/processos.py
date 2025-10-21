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
from shared.models.juridico import ProcessoJuridico
from services.legal.schemas.processo import (
    ProcessoJuridicoCreate,
    ProcessoJuridicoUpdate,
    ProcessoJuridicoResponse,
    ProcessoHistorico,
)

router = APIRouter()


@router.get("/", response_model=List[ProcessoJuridicoResponse])
async def list_processos(
    empresa_id: UUID,
    tipo: Optional[str] = None,
    status: Optional[str] = None,
    risco: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """List legal processes with filters."""
    query = select(ProcessoJuridico).where(
        ProcessoJuridico.empresa_id == empresa_id
    )

    if tipo:
        query = query.where(ProcessoJuridico.tipo == tipo)

    if status:
        query = query.where(ProcessoJuridico.status == status)

    if risco:
        query = query.where(ProcessoJuridico.risco == risco)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/proximas-acoes")
async def get_proximas_acoes(
    empresa_id: UUID,
    dias: int = 30,
    db: AsyncSession = Depends(get_db),
):
    """Get processes with upcoming actions."""
    data_limite = date.today().replace(day=date.today().day + dias)

    query = select(ProcessoJuridico).where(
        and_(
            ProcessoJuridico.empresa_id == empresa_id,
            ProcessoJuridico.status == "andamento",
            ProcessoJuridico.proxima_acao != None,
            ProcessoJuridico.proxima_acao <= data_limite
        )
    ).order_by(ProcessoJuridico.proxima_acao)

    result = await db.execute(query)
    processos = result.scalars().all()

    return [
        {
            "id": p.id,
            "numero_processo": p.numero_processo,
            "tipo": p.tipo,
            "parte_contraria": p.parte_contraria,
            "proxima_acao": p.proxima_acao,
            "proxima_acao_descricao": p.proxima_acao_descricao,
            "dias_restantes": (p.proxima_acao - date.today()).days,
            "risco": p.risco,
            "advogado_responsavel": p.advogado_responsavel
        }
        for p in processos
    ]


@router.get("/{processo_id}", response_model=ProcessoJuridicoResponse)
async def get_processo(
    processo_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific legal process."""
    result = await db.execute(
        select(ProcessoJuridico).where(ProcessoJuridico.id == processo_id)
    )
    processo = result.scalar_one_or_none()

    if not processo:
        raise HTTPException(status_code=404, detail="Process not found")

    return processo


@router.post("/", response_model=ProcessoJuridicoResponse)
async def create_processo(
    processo: ProcessoJuridicoCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new legal process."""
    # Check if process number already exists
    if processo.numero_processo:
        existing = await db.execute(
            select(ProcessoJuridico).where(
                ProcessoJuridico.numero_processo == processo.numero_processo
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Process number already exists"
            )

    db_processo = ProcessoJuridico(**processo.dict())
    db.add(db_processo)
    await db.commit()
    await db.refresh(db_processo)
    return db_processo


@router.put("/{processo_id}", response_model=ProcessoJuridicoResponse)
async def update_processo(
    processo_id: UUID,
    processo_update: ProcessoJuridicoUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a legal process."""
    result = await db.execute(
        select(ProcessoJuridico).where(ProcessoJuridico.id == processo_id)
    )
    processo = result.scalar_one_or_none()

    if not processo:
        raise HTTPException(status_code=404, detail="Process not found")

    for field, value in processo_update.dict(exclude_unset=True).items():
        setattr(processo, field, value)

    await db.commit()
    await db.refresh(processo)
    return processo


@router.post("/{processo_id}/adicionar-historico")
async def adicionar_historico(
    processo_id: UUID,
    historico: ProcessoHistorico,
    db: AsyncSession = Depends(get_db),
):
    """Add history entry to a legal process."""
    result = await db.execute(
        select(ProcessoJuridico).where(ProcessoJuridico.id == processo_id)
    )
    processo = result.scalar_one_or_none()

    if not processo:
        raise HTTPException(status_code=404, detail="Process not found")

    if not processo.historico:
        processo.historico = []

    processo.historico.append({
        "data": str(historico.data),
        "evento": historico.evento,
        "descricao": historico.descricao,
        "responsavel": historico.responsavel
    })

    await db.commit()

    return {"message": "History entry added successfully"}


@router.get("/relatorio/riscos")
async def get_relatorio_riscos(
    empresa_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get risk report for all processes."""
    query = select(ProcessoJuridico).where(
        ProcessoJuridico.empresa_id == empresa_id,
        ProcessoJuridico.status == "andamento"
    )

    result = await db.execute(query)
    processos = result.scalars().all()

    # Aggregate by risk level
    riscos = {
        "baixo": {"quantidade": 0, "valor_total": 0},
        "medio": {"quantidade": 0, "valor_total": 0},
        "alto": {"quantidade": 0, "valor_total": 0}
    }

    for processo in processos:
        if processo.risco in riscos:
            riscos[processo.risco]["quantidade"] += 1
            if processo.valor_causa:
                riscos[processo.risco]["valor_total"] += float(processo.valor_causa)

    # Aggregate by type
    tipos = {}
    for processo in processos:
        if processo.tipo not in tipos:
            tipos[processo.tipo] = {"quantidade": 0, "valor_total": 0}

        tipos[processo.tipo]["quantidade"] += 1
        if processo.valor_causa:
            tipos[processo.tipo]["valor_total"] += float(processo.valor_causa)

    return {
        "empresa_id": empresa_id,
        "total_processos": len(processos),
        "riscos": riscos,
        "tipos": tipos,
        "valor_total_em_risco": sum(
            float(p.valor_causa) for p in processos if p.valor_causa
        )
    }