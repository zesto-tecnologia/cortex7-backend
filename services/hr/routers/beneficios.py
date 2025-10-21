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
from shared.models.rh import Funcionario

router = APIRouter()


class BeneficioUpdate(BaseModel):
    """Benefit update schema."""
    vale_transporte: bool = False
    valor_vt: float = 0
    vale_alimentacao: bool = False
    valor_va: float = 0
    plano_saude: bool = False
    plano_saude_tipo: str = ""
    plano_odontologico: bool = False
    seguro_vida: bool = False
    outros: Dict[str, Any] = {}


@router.get("/funcionario/{funcionario_id}")
async def get_beneficios_funcionario(
    funcionario_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get benefits for a specific employee."""
    result = await db.execute(
        select(Funcionario).where(Funcionario.id == funcionario_id)
    )
    funcionario = result.scalar_one_or_none()

    if not funcionario:
        raise HTTPException(status_code=404, detail="Employee not found")

    return funcionario.beneficios or {}


@router.put("/funcionario/{funcionario_id}")
async def update_beneficios_funcionario(
    funcionario_id: UUID,
    beneficios: BeneficioUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update benefits for an employee."""
    result = await db.execute(
        select(Funcionario).where(Funcionario.id == funcionario_id)
    )
    funcionario = result.scalar_one_or_none()

    if not funcionario:
        raise HTTPException(status_code=404, detail="Employee not found")

    funcionario.beneficios = beneficios.dict()
    await db.commit()

    return {
        "message": "Benefits updated successfully",
        "beneficios": funcionario.beneficios
    }


@router.get("/relatorio/{empresa_id}")
async def get_relatorio_beneficios(
    empresa_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Generate benefits report for the company."""
    query = select(Funcionario).where(
        Funcionario.empresa_id == empresa_id,
        Funcionario.status == "ativo"
    )

    result = await db.execute(query)
    funcionarios = result.scalars().all()

    # Aggregate benefits data
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
        if func.beneficios:
            if func.beneficios.get("vale_transporte"):
                beneficios_stats["vale_transporte"] += 1
                beneficios_stats["custo_total_vt"] += func.beneficios.get("valor_vt", 0)

            if func.beneficios.get("vale_alimentacao"):
                beneficios_stats["vale_alimentacao"] += 1
                beneficios_stats["custo_total_va"] += func.beneficios.get("valor_va", 0)

            if func.beneficios.get("plano_saude"):
                beneficios_stats["plano_saude"] += 1

            if func.beneficios.get("plano_odontologico"):
                beneficios_stats["plano_odontologico"] += 1

            if func.beneficios.get("seguro_vida"):
                beneficios_stats["seguro_vida"] += 1

    return {
        "empresa_id": empresa_id,
        "total_funcionarios": total_funcionarios,
        "beneficios": {
            "vale_transporte": {
                "quantidade": beneficios_stats["vale_transporte"],
                "percentual": (beneficios_stats["vale_transporte"] / total_funcionarios * 100) if total_funcionarios > 0 else 0,
                "custo_mensal": beneficios_stats["custo_total_vt"]
            },
            "vale_alimentacao": {
                "quantidade": beneficios_stats["vale_alimentacao"],
                "percentual": (beneficios_stats["vale_alimentacao"] / total_funcionarios * 100) if total_funcionarios > 0 else 0,
                "custo_mensal": beneficios_stats["custo_total_va"]
            },
            "plano_saude": {
                "quantidade": beneficios_stats["plano_saude"],
                "percentual": (beneficios_stats["plano_saude"] / total_funcionarios * 100) if total_funcionarios > 0 else 0
            },
            "plano_odontologico": {
                "quantidade": beneficios_stats["plano_odontologico"],
                "percentual": (beneficios_stats["plano_odontologico"] / total_funcionarios * 100) if total_funcionarios > 0 else 0
            },
            "seguro_vida": {
                "quantidade": beneficios_stats["seguro_vida"],
                "percentual": (beneficios_stats["seguro_vida"] / total_funcionarios * 100) if total_funcionarios > 0 else 0
            }
        },
        "custo_total_mensal": beneficios_stats["custo_total_vt"] + beneficios_stats["custo_total_va"]
    }