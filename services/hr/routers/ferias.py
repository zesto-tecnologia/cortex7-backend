"""
Férias (Vacation) management router.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from datetime import date, timedelta
from pydantic import BaseModel

from shared.database.connection import get_db
from shared.models.rh import Funcionario

router = APIRouter()


class FeriasRequest(BaseModel):
    """Vacation request schema."""
    funcionario_id: UUID
    data_inicio: date
    data_fim: date
    tipo: str = "ferias"  # ferias, licenca, abono


class FeriasResponse(BaseModel):
    """Vacation response schema."""
    funcionario_id: UUID
    periodo_aquisitivo: str
    dias_disponiveis: int
    dias_utilizados: int
    historico: List[dict]


@router.post("/solicitar")
async def solicitar_ferias(
    request: FeriasRequest,
    db: AsyncSession = Depends(get_db),
):
    """Request vacation days."""
    # Get employee
    result = await db.execute(
        select(Funcionario).where(Funcionario.id == request.funcionario_id)
    )
    funcionario = result.scalar_one_or_none()

    if not funcionario:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Calculate requested days
    dias_solicitados = (request.data_fim - request.data_inicio).days + 1

    # Check available days
    if not funcionario.ferias:
        funcionario.ferias = {"historico": [], "dias_disponiveis": 30}

    dias_disponiveis = funcionario.ferias.get("dias_disponiveis", 30)

    if dias_solicitados > dias_disponiveis:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient vacation days. Available: {dias_disponiveis}"
        )

    # Register vacation request
    novo_periodo = {
        "data_inicio": str(request.data_inicio),
        "data_fim": str(request.data_fim),
        "dias": dias_solicitados,
        "tipo": request.tipo,
        "status": "aprovado",
        "aprovado_em": str(date.today())
    }

    funcionario.ferias["historico"].append(novo_periodo)
    funcionario.ferias["dias_disponiveis"] = dias_disponiveis - dias_solicitados

    await db.commit()

    return {
        "message": "Vacation request approved",
        "dias_solicitados": dias_solicitados,
        "dias_restantes": funcionario.ferias["dias_disponiveis"]
    }


@router.get("/funcionario/{funcionario_id}", response_model=FeriasResponse)
async def get_ferias_funcionario(
    funcionario_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get vacation information for an employee."""
    result = await db.execute(
        select(Funcionario).where(Funcionario.id == funcionario_id)
    )
    funcionario = result.scalar_one_or_none()

    if not funcionario:
        raise HTTPException(status_code=404, detail="Employee not found")

    if not funcionario.ferias:
        funcionario.ferias = {"historico": [], "dias_disponiveis": 30}

    # Calculate acquisition period
    from datetime import datetime

    if funcionario.data_admissao:
        periodo_inicio = funcionario.data_admissao
        periodo_fim = periodo_inicio + timedelta(days=365)
        periodo_aquisitivo = f"{periodo_inicio} - {periodo_fim}"
    else:
        periodo_aquisitivo = "Not defined"

    dias_utilizados = sum(
        periodo.get("dias", 0)
        for periodo in funcionario.ferias.get("historico", [])
    )

    return FeriasResponse(
        funcionario_id=funcionario_id,
        periodo_aquisitivo=periodo_aquisitivo,
        dias_disponiveis=funcionario.ferias.get("dias_disponiveis", 30),
        dias_utilizados=dias_utilizados,
        historico=funcionario.ferias.get("historico", [])
    )


@router.get("/calendario/{empresa_id}")
async def get_calendario_ferias(
    empresa_id: UUID,
    ano: int = 2025,
    db: AsyncSession = Depends(get_db),
):
    """Get vacation calendar for the company."""
    query = select(Funcionario).where(
        Funcionario.empresa_id == empresa_id,
        Funcionario.status == "ativo"
    )

    result = await db.execute(query)
    funcionarios = result.scalars().all()

    calendario = []
    for func in funcionarios:
        if func.ferias and func.ferias.get("historico"):
            for periodo in func.ferias["historico"]:
                # Filter by year
                if periodo.get("data_inicio", "").startswith(str(ano)):
                    calendario.append({
                        "funcionario_id": func.id,
                        "funcionario_cpf": func.cpf,
                        "cargo": func.cargo,
                        "data_inicio": periodo.get("data_inicio"),
                        "data_fim": periodo.get("data_fim"),
                        "dias": periodo.get("dias"),
                        "tipo": periodo.get("tipo", "ferias"),
                        "status": periodo.get("status", "aprovado")
                    })

    # Sort by start date
    calendario.sort(key=lambda x: x.get("data_inicio", ""))

    return calendario