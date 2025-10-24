"""
Benefícios (Benefits) management router.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from uuid import UUID
from pydantic import BaseModel

from shared.database.connection import get_db
from shared.models.hr import Employee

router = APIRouter()


class BenefitsUpdateSchema(BaseModel):
    """Benefit update schema."""
    vale_transporte: bool = False
    transportation_value: float = 0
    vale_alimentacao: bool = False
    food_value: float = 0
    plano_saude: bool = False
    plano_saude_tipo: str = ""
    plano_odontologico: bool = False
    seguro_vida: bool = False
    outros: Dict[str, Any] = {}


@router.get("/employee/{employee_id}")
async def get_benefits_for_employee(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get benefits for a specific employee."""
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    employee = result.scalar_one_or_none()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    return employee.benefits or {}


@router.put("/employee/{employee_id}")
async def update_benefits_for_employee(
    employee_id: UUID,
    benefits: BenefitsUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    """Update benefits for an employee."""
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    employee = result.scalar_one_or_none()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    employee.benefits = benefits.dict()
    await db.commit()

    return {
        "message": "Benefits updated successfully",
        "benefits": employee.benefits
    }


@router.get("/report/{company_id}")
async def get_benefits_report(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Generate benefits report for the company."""
    query = select(Employee).where(
        Employee.company_id == company_id,
        Employee.status == "active"
    )

    result = await db.execute(query)
    employees = result.scalars().all()

    # Aggregate benefits date
    total_employees = len(employees)
    benefits_stats = {
        "vale_transporte": 0,
        "vale_alimentacao": 0,
        "plano_saude": 0,
        "plano_odontologico": 0,
        "seguro_vida": 0,
        "custo_total_vt": 0,
        "custo_total_va": 0,
    }

    for employee in employees:
        if employee.benefits:
            if employee.benefits.get("vale_transporte"):
                benefits_stats["vale_transporte"] += 1
                benefits_stats["custo_total_vt"] += employee.benefits.get("transportation_value", 0)

            if employee.benefits.get("vale_alimentacao"):
                benefits_stats["vale_alimentacao"] += 1
                benefits_stats["custo_total_va"] += employee.benefits.get("food_value", 0)

            if employee.benefits.get("plano_saude"):
                benefits_stats["plano_saude"] += 1

            if employee.benefits.get("plano_odontologico"):
                benefits_stats["plano_odontologico"] += 1

            if employee.benefits.get("seguro_vida"):
                benefits_stats["seguro_vida"] += 1

    return {
        "company_id": company_id,
        "total_employees": total_employees,
        "benefits": {
            "vale_transporte": {
                "quantity": benefits_stats["vale_transporte"],
                "percentage": (benefits_stats["vale_transporte"] / total_employees * 100) if total_employees > 0 else 0,
                "custo_mensal": benefits_stats["custo_total_vt"]
            },
            "vale_alimentacao": {
                "quantity": benefits_stats["vale_alimentacao"],
                "percentage": (benefits_stats["vale_alimentacao"] / total_employees * 100) if total_employees > 0 else 0,
                "custo_mensal": benefits_stats["custo_total_va"]
            },
            "plano_saude": {
                "quantity": benefits_stats["plano_saude"],
                "percentage": (benefits_stats["plano_saude"] / total_employees * 100) if total_employees > 0 else 0
            },
            "plano_odontologico": {
                "quantity": benefits_stats["plano_odontologico"],
                "percentage": (benefits_stats["plano_odontologico"] / total_employees * 100) if total_employees > 0 else 0
            },
            "seguro_vida": {
                "quantity": benefits_stats["seguro_vida"],
                "percentage": (benefits_stats["seguro_vida"] / total_employees * 100) if total_employees > 0 else 0
            }
        },
        "custo_total_mensal": benefits_stats["custo_total_vt"] + benefits_stats["custo_total_va"]
    }