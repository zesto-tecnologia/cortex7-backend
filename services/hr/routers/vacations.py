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


class VacationRequest(BaseModel):
    """Vacation request schema."""
    employee_id: UUID
    start_date: date
    end_date: date
    type: str = "vacations"  # vacations, licenca, abono


class VacationResponse(BaseModel):
    """Vacation response schema."""
    employee_id: UUID
    periodo_aquisitivo: str
    dias_disponiveis: int
    dias_utilizados: int
    historico: List[dict]


@router.post("/request")
async def request_vacation(
    request: VacationRequest,
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
        employee.vacations = {"history": [], "available_days": 30}

    available_days = employee.vacations.get("available_days", 30)

    if days_requested > available_days:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient vacation days. Available: {available_days}"
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
    employee.vacations["available_days"] = available_days - days_requested

    await db.commit()

    return {
        "message": "Vacation request approved",
        "days_requested": days_requested,
        "remaining_days": employee.vacations["available_days"]
    }


@router.get("/employee/{employee_id}", response_model=VacationResponse)
async def get_vacation(
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
        employee.vacations = {"history": [], "available_days": 30}

    # Calculate acquisition period
    from datetime import datetime

    if employee.hire_date:
        period_start = employee.hire_date
        period_end = period_start + timedelta(days=365)
        acquisition_period = f"{period_start} - {period_end}"
    else:
        acquisition_period = "Not defined"

    used_days = sum(
        vacation.get("days", 0)
        for vacation in employee.vacations.get("history", [])
    )

    return VacationResponse(
        employee_id=employee_id,
        acquisition_period=acquisition_period,
        available_days=employee.vacations.get("available_days", 30),
        used_days=used_days,
        history=employee.vacations.get("history", [])
    )


@router.get("/calendar/{company_id}")
async def get_vacation_calendar(
    company_id: UUID,
    ano: int = 2025,
    db: AsyncSession = Depends(get_db),
):
    """Get vacation calendar for the company."""
    query = select(Employee).where(
        Employee.company_id == company_id,
        Employee.status == "active"
    )

    result = await db.execute(query)
    employees = result.scalars().all()

    calendar = []
    for employee in employees:
        if employee.vacations and employee.vacations.get("history"):
            for vacation in employee.vacations["history"]:
                # Filter by year
                if vacation.get("start_date", "").startswith(str(ano)):
                    calendar.append({
                        "employee_id": employee.id,
                        "employee_cpf": employee.cpf,
                        "position": employee.position,
                        "start_date": vacation.get("start_date"),
                        "end_date": vacation.get("end_date"),
                        "days": vacation.get("days"),
                        "type": vacation.get("type", "vacations"),
                        "status": vacation.get("status", "approved")
                    })

    # Sort by start date
    calendar.sort(key=lambda x: x.get("start_date", ""))

    return calendar