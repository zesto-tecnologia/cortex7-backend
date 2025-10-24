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
from shared.models.hr import Employee

router = APIRouter()


class FeriasRequest(BaseModel):
    """Vacation request schema."""
    employee_id: UUID
    start_date: date
    end_date: date
    type: str = "vacations"  # vacations, licenca, abono


class FeriasResponse(BaseModel):
    """Vacation response schema."""
    employee_id: UUID
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
        select(Employee).where(Employee.id == request.employee_id)
    )
    employee = result.scalar_one_or_none()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Calculate requested days
    days_requested = (request.end_date - request.start_date).days + 1

    # Check available days
    if not employee.vacations:
        employee.vacations = {"history": [], "dias_disponiveis": 30}

    dias_disponiveis = employee.vacations.get("dias_disponiveis", 30)

    if days_requested > dias_disponiveis:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient vacation days. Available: {dias_disponiveis}"
        )

    # Register vacation request
    novo_periodo = {
        "start_date": str(request.start_date),
        "end_date": str(request.end_date),
        "dias": days_requested,
        "type": request.type,
        "status": "approved",
        "approved_at": str(date.today())
    }

    employee.vacations["history"].append(novo_periodo)
    employee.vacations["dias_disponiveis"] = dias_disponiveis - days_requested

    await db.commit()

    return {
        "message": "Vacation request approved",
        "days_requested": days_requested,
        "dias_restantes": employee.vacations["dias_disponiveis"]
    }


@router.get("/employee/{employee_id}", response_model=FeriasResponse)
async def get_ferias_funcionario(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get vacation information for an employee."""
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    employee = result.scalar_one_or_none()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if not employee.vacations:
        employee.vacations = {"history": [], "dias_disponiveis": 30}

    # Calculate acquisition period
    from datetime import datetime

    if employee.admission_date:
        period_start = employee.admission_date
        periodo_fim = period_start + timedelta(days=365)
        periodo_aquisitivo = f"{period_start} - {periodo_fim}"
    else:
        periodo_aquisitivo = "Not defined"

    dias_utilizados = sum(
        periodo.get("dias", 0)
        for periodo in employee.vacations.get("history", [])
    )

    return FeriasResponse(
        employee_id=employee_id,
        periodo_aquisitivo=periodo_aquisitivo,
        dias_disponiveis=employee.vacations.get("dias_disponiveis", 30),
        dias_utilizados=dias_utilizados,
        historico=employee.vacations.get("history", [])
    )


@router.get("/calendar/{company_id}")
async def get_calendario_ferias(
    company_id: UUID,
    ano: int = 2025,
    db: AsyncSession = Depends(get_db),
):
    """Get vacation calendar for the company."""
    query = select(Employee).where(
        Employee.company_id == company_id,
        Employee.status == "ativo"
    )

    result = await db.execute(query)
    funcionarios = result.scalars().all()

    calendario = []
    for func in funcionarios:
        if func.vacations and func.vacations.get("history"):
            for periodo in func.vacations["history"]:
                # Filter by year
                if periodo.get("start_date", "").startswith(str(ano)):
                    calendario.append({
                        "employee_id": func.id,
                        "funcionario_cpf": func.cpf,
                        "cargo": func.cargo,
                        "start_date": periodo.get("start_date"),
                        "end_date": periodo.get("end_date"),
                        "dias": periodo.get("dias"),
                        "type": periodo.get("type", "vacations"),
                        "status": periodo.get("status", "approved")
                    })

    # Sort by start date
    calendario.sort(key=lambda x: x.get("start_date", ""))

    return calendario