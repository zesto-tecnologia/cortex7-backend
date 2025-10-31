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
async def list_employees(
    company_id: UUID,
    department_id: Optional[UUID] = None,
    status: Optional[str] = "active",
    position: Optional[str] = None,
    contract_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """List employees with filters."""
    query = select(Employee).where(
        Employee.company_id == company_id,
        Employee.status == status
    )

    if department_id:
        query = query.where(Employee.department_id == department_id)

    if position:
        query = query.where(Employee.position.ilike(f"%{position}%"))

    if contract_type:
        query = query.where(Employee.contract_type == contract_type)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/search")
async def search_employees(
    company_id: UUID,
    q: str,
    db: AsyncSession = Depends(get_db),
):
    """Search employees by name, tax_id, or position."""
    query = select(Employee).where(
        Employee.company_id == company_id,
        or_(
            Employee.name.ilike(f"%{q}%"),
            Employee.tax_id.contains(q),
            Employee.position.ilike(f"%{q}%")
        )
    )

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{employee_id}", response_model=EmployeeWithContracts)
async def get_employee(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific employee with contracts."""
    from sqlalchemy.orm import selectinload

    query = select(Employee).options(
        selectinload(Employee.employment_contracts),
        selectinload(Employee.user),
        selectinload(Employee.department)
    ).where(Employee.id == employee_id)

    result = await db.execute(query)
    employee = result.scalar_one_or_none()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    return employee


@router.post("/", response_model=EmployeeResponse)
async def create_employee(
    employee: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new employee."""
    # Check if tax_id already exists
    existing = await db.execute(
        select(Employee).where(Employee.tax_id == employee.tax_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Tax ID already registered")

    db_employee = Employee(**employee.dict())
    db.add(db_employee)
    await db.commit()
    await db.refresh(db_employee)
    return db_employee


@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: UUID,
    employee_update: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an employee."""
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    employee = result.scalar_one_or_none()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    for field, value in employee_update.dict(exclude_unset=True).items():
        setattr(employee, field, value)

    await db.commit()
    await db.refresh(employee)
    return employee


@router.post("/{employee_id}/termination")
async def register_termination(
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


@router.get("/{employee_id}/available-vacations")
async def get_available_vacations(
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

    if employee.hire_date:
        months_employed = (
            (datetime.now().date() - employee.hire_date).days / 30
        )
        vacation_periods = int(months_employed / 12)
        available_days = vacation_periods * 30  # 30 days per year in Brazil

        # Subtract used vacation days from vacations JSON field
        used_days = 0
        if employee.vacations:
            for vacation in employee.vacations.get("history", []):
                used_days += vacation.get("days", 0)

        return {
            "employee_id": employee_id,
            "months_employed": int(months_employed),
            "vacation_periods": vacation_periods,
            "available_days": available_days,
            "used_days": used_days,
            "remaining_days": available_days - used_days
        }

    return {
        "employee_id": employee_id,
        "months_employed": 0,
        "vacation_periods": 0,
        "available_days": 0,
        "used_days": 0,
        "remaining_days": 0
    }