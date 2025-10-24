"""
Funcionários (Employees) router.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from datetime import date
from uuid import UUID

from shared.database.connection import get_db
from shared.models.hr import Employee
from services.hr.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeWithContracts,
)

router = APIRouter()


@router.get("/", response_model=List[EmployeeResponse])
async def list_funcionarios(
    company_id: UUID,
    departamento_id: Optional[UUID] = None,
    status: Optional[str] = "ativo",
    cargo: Optional[str] = None,
    tipo_contrato: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """List employees with filters."""
    query = select(Employee).where(
        Employee.company_id == company_id,
        Employee.status == status
    )

    if departamento_id:
        query = query.where(Employee.departamento_id == departamento_id)

    if cargo:
        query = query.where(Employee.cargo.ilike(f"%{cargo}%"))

    if tipo_contrato:
        query = query.where(Employee.tipo_contrato == tipo_contrato)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/search")
async def search_funcionarios(
    company_id: UUID,
    q: str,
    db: AsyncSession = Depends(get_db),
):
    """Search employees by name or CPF."""
    query = select(Employee).where(
        Employee.company_id == company_id,
        or_(
            Employee.cpf.contains(q),
            Employee.cargo.ilike(f"%{q}%")
        )
    )

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{employee_id}", response_model=EmployeeWithContracts)
async def get_funcionario(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific employee with contracts."""
    from sqlalchemy.orm import selectinload

    query = select(Employee).options(
        selectinload(Employee.contratos_trabalho),
        selectinload(Employee.user),
        selectinload(Employee.departamento)
    ).where(Employee.id == employee_id)

    result = await db.execute(query)
    employee = result.scalar_one_or_none()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    return employee


@router.post("/", response_model=EmployeeResponse)
async def create_funcionario(
    employee: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new employee."""
    # Check if CPF already exists
    existing = await db.execute(
        select(Employee).where(Employee.cpf == employee.cpf)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="CPF already registered")

    db_funcionario = Employee(**employee.dict())
    db.add(db_funcionario)
    await db.commit()
    await db.refresh(db_funcionario)
    return db_funcionario


@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_funcionario(
    employee_id: UUID,
    funcionario_update: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an employee."""
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    employee = result.scalar_one_or_none()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    for field, value in funcionario_update.dict(exclude_unset=True).items():
        setattr(employee, field, value)

    await db.commit()
    await db.refresh(employee)
    return employee


@router.post("/{employee_id}/demissao")
async def registrar_demissao(
    employee_id: UUID,
    termination_date: date,
    db: AsyncSession = Depends(get_db),
):
    """Register employee termination."""
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    employee = result.scalar_one_or_none()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    employee.termination_date = termination_date
    employee.status = "inativo"

    await db.commit()

    return {"message": "Termination registered successfully"}


@router.get("/{employee_id}/vacations-disponiveis")
async def get_ferias_disponiveis(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get available vacation days for an employee."""
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    employee = result.scalar_one_or_none()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Calculate vacation days based on employment time
    from datetime import datetime

    if employee.admission_date:
        months_employed = (
            (datetime.now().date() - employee.admission_date).days / 30
        )
        vacation_periods = int(months_employed / 12)
        available_days = vacation_periods * 30  # 30 days per year in Brazil

        # Subtract used vacation days from vacations JSON field
        used_days = 0
        if employee.vacations:
            for periodo in employee.vacations.get("history", []):
                used_days += periodo.get("dias", 0)

        return {
            "employee_id": employee_id,
            "months_employed": int(months_employed),
            "vacation_periods": vacation_periods,
            "total_earned_days": available_days,
            "used_days": used_days,
            "available_days": available_days - used_days
        }

    return {"available_days": 0}