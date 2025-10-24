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


class BeneficioUpdate(BaseModel):
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
async def get_beneficios_funcionario(
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
async def update_beneficios_funcionario(
    employee_id: UUID,
    benefits: BeneficioUpdate,
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
async def get_relatorio_beneficios(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Generate benefits report for the company."""
    query = select(Employee).where(
        Employee.company_id == company_id,
        Employee.status == "ativo"
    )

    result = await db.execute(query)
    funcionarios = result.scalars().all()

    # Aggregate benefits date
    total_funcionarios = len(funcionarios)
    beneficios_stats = {
        "vale_transporte": 0,
        "vale_alimentacao": 0,
        "plano_saude": 0,
        "plano_odontologico": 0,
        "seguro_vida": 0,
        "custo_total_vt": 0,
        "custo_total_va": 0,
    }

    for func in funcionarios:
        if func.benefits:
            if func.benefits.get("vale_transporte"):
                beneficios_stats["vale_transporte"] += 1
                beneficios_stats["custo_total_vt"] += func.benefits.get("transportation_value", 0)

            if func.benefits.get("vale_alimentacao"):
                beneficios_stats["vale_alimentacao"] += 1
                beneficios_stats["custo_total_va"] += func.benefits.get("food_value", 0)

            if func.benefits.get("plano_saude"):
                beneficios_stats["plano_saude"] += 1

            if func.benefits.get("plano_odontologico"):
                beneficios_stats["plano_odontologico"] += 1

            if func.benefits.get("seguro_vida"):
                beneficios_stats["seguro_vida"] += 1

    return {
        "company_id": company_id,
        "total_funcionarios": total_funcionarios,
        "benefits": {
            "vale_transporte": {
                "quantity": beneficios_stats["vale_transporte"],
                "percentage": (beneficios_stats["vale_transporte"] / total_funcionarios * 100) if total_funcionarios > 0 else 0,
                "custo_mensal": beneficios_stats["custo_total_vt"]
            },
            "vale_alimentacao": {
                "quantity": beneficios_stats["vale_alimentacao"],
                "percentage": (beneficios_stats["vale_alimentacao"] / total_funcionarios * 100) if total_funcionarios > 0 else 0,
                "custo_mensal": beneficios_stats["custo_total_va"]
            },
            "plano_saude": {
                "quantity": beneficios_stats["plano_saude"],
                "percentage": (beneficios_stats["plano_saude"] / total_funcionarios * 100) if total_funcionarios > 0 else 0
            },
            "plano_odontologico": {
                "quantity": beneficios_stats["plano_odontologico"],
                "percentage": (beneficios_stats["plano_odontologico"] / total_funcionarios * 100) if total_funcionarios > 0 else 0
            },
            "seguro_vida": {
                "quantity": beneficios_stats["seguro_vida"],
                "percentage": (beneficios_stats["seguro_vida"] / total_funcionarios * 100) if total_funcionarios > 0 else 0
            }
        },
        "custo_total_mensal": beneficios_stats["custo_total_vt"] + beneficios_stats["custo_total_va"]
    }