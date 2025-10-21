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
from shared.models.juridico import Contrato, ProcessoJuridico

router = APIRouter()


@router.get("/todos/{empresa_id}")
async def get_todos_prazos(
    empresa_id: UUID,
    dias_limite: int = 90,
    db: AsyncSession = Depends(get_db),
):
    """Get all deadlines and important dates."""
    data_limite = date.today() + timedelta(days=dias_limite)
    prazos = []

    # Contract deadlines
    contratos_query = select(Contrato).where(
        and_(
            Contrato.empresa_id == empresa_id,
            Contrato.status == "vigente",
            Contrato.data_fim != None,
            Contrato.data_fim <= data_limite
        )
    )
    contratos_result = await db.execute(contratos_query)
    contratos = contratos_result.scalars().all()

    for contrato in contratos:
        dias_restantes = (contrato.data_fim - date.today()).days

        prazos.append({
            "tipo": "contrato_vencimento",
            "entidade_id": contrato.id,
            "descricao": f"Vencimento contrato: {contrato.parte_contraria}",
            "data": contrato.data_fim,
            "dias_restantes": dias_restantes,
            "prioridade": "alta" if dias_restantes <= 15 else "media",
            "renovacao_automatica": contrato.renovacao_automatica
        })

        # Contract critical deadlines
        if contrato.prazos_importantes:
            for prazo in contrato.prazos_importantes:
                prazo_data = date.fromisoformat(prazo["data"])
                if prazo_data <= data_limite:
                    dias_restantes = (prazo_data - date.today()).days
                    prazos.append({
                        "tipo": "contrato_prazo_critico",
                        "entidade_id": contrato.id,
                        "descricao": prazo["descricao"],
                        "data": prazo_data,
                        "dias_restantes": dias_restantes,
                        "prioridade": "alta" if dias_restantes <= 7 else "media",
                        "notificado": prazo.get("notificado", False)
                    })

    # Legal process deadlines
    processos_query = select(ProcessoJuridico).where(
        and_(
            ProcessoJuridico.empresa_id == empresa_id,
            ProcessoJuridico.status == "andamento",
            ProcessoJuridico.proxima_acao != None,
            ProcessoJuridico.proxima_acao <= data_limite
        )
    )
    processos_result = await db.execute(processos_query)
    processos = processos_result.scalars().all()

    for processo in processos:
        dias_restantes = (processo.proxima_acao - date.today()).days

        prazos.append({
            "tipo": "processo_acao",
            "entidade_id": processo.id,
            "descricao": processo.proxima_acao_descricao or f"Ação processo: {processo.numero_processo}",
            "data": processo.proxima_acao,
            "dias_restantes": dias_restantes,
            "prioridade": "critica" if dias_restantes <= 3 else "alta" if dias_restantes <= 7 else "media",
            "risco_processo": processo.risco
        })

    # Sort by date
    prazos.sort(key=lambda x: x["data"])

    return prazos


@router.get("/criticos/{empresa_id}")
async def get_prazos_criticos(
    empresa_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get critical deadlines (next 7 days)."""
    prazos_todos = await get_todos_prazos(empresa_id, dias_limite=7, db=db)

    # Filter only high priority
    prazos_criticos = [
        p for p in prazos_todos
        if p["prioridade"] in ["critica", "alta"]
    ]

    return {
        "total_criticos": len(prazos_criticos),
        "prazos": prazos_criticos
    }


@router.get("/calendario/{empresa_id}")
async def get_calendario_prazos(
    empresa_id: UUID,
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
    prazos_todos = await get_todos_prazos(empresa_id, dias_limite=365, db=db)

    # Filter by date range
    calendario = {}
    for prazo in prazos_todos:
        if start_date <= prazo["data"] <= end_date:
            data_str = str(prazo["data"])
            if data_str not in calendario:
                calendario[data_str] = []
            calendario[data_str].append(prazo)

    return calendario


@router.post("/marcar-notificado/{empresa_id}")
async def marcar_prazo_notificado(
    empresa_id: UUID,
    tipo_entidade: str,  # "contrato" or "processo"
    entidade_id: UUID,
    prazo_descricao: str,
    db: AsyncSession = Depends(get_db),
):
    """Mark a deadline as notified."""
    if tipo_entidade == "contrato":
        result = await db.execute(
            select(Contrato).where(
                and_(
                    Contrato.id == entidade_id,
                    Contrato.empresa_id == empresa_id
                )
            )
        )
        contrato = result.scalar_one_or_none()

        if not contrato:
            raise HTTPException(status_code=404, detail="Contract not found")

        if contrato.prazos_importantes:
            for prazo in contrato.prazos_importantes:
                if prazo["descricao"] == prazo_descricao:
                    prazo["notificado"] = True
                    break

        await db.commit()
        return {"message": "Deadline marked as notified"}

    else:
        raise HTTPException(status_code=400, detail="Invalid entity type")