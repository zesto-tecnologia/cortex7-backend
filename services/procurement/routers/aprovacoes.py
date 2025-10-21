"""
Aprovações (Approvals) workflow router.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Dict
from datetime import date
from uuid import UUID

from shared.database.connection import get_db
from shared.models.suprimentos import OrdemCompra
from shared.models.usuario import Usuario

router = APIRouter()


@router.get("/workflow-config")
async def get_workflow_config():
    """Get approval workflow configuration."""
    return {
        "niveis": [
            {
                "nivel": 1,
                "nome": "Supervisor",
                "limite_min": 0,
                "limite_max": 10000,
                "alcada_requerida": "supervisor"
            },
            {
                "nivel": 2,
                "nome": "Gerente",
                "limite_min": 10001,
                "limite_max": 50000,
                "alcada_requerida": "gerente"
            },
            {
                "nivel": 3,
                "nome": "Diretor",
                "limite_min": 50001,
                "limite_max": 200000,
                "alcada_requerida": "diretor"
            },
            {
                "nivel": 4,
                "nome": "Presidente",
                "limite_min": 200001,
                "limite_max": None,
                "alcada_requerida": "presidente"
            }
        ],
        "regras": [
            "Ordens acima de R$ 10.000 requerem 2 aprovações",
            "Ordens acima de R$ 50.000 requerem aprovação do diretor",
            "Ordens acima de R$ 200.000 requerem aprovação do presidente",
            "Compras emergenciais podem pular um nível com justificativa"
        ]
    }


@router.get("/pendentes/{usuario_id}")
async def get_aprovacoes_pendentes(
    usuario_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all pending approvals for a user."""
    # Get user
    user_result = await db.execute(
        select(Usuario).where(Usuario.id == usuario_id)
    )
    usuario = user_result.scalar_one_or_none()

    if not usuario:
        raise HTTPException(status_code=404, detail="User not found")

    aprovacoes_pendentes = []

    # Purchase Orders
    alcada_suprimentos = usuario.alcadas.get("suprimentos", 0) if usuario.alcadas else 0

    if alcada_suprimentos > 0:
        ordens_query = select(OrdemCompra).where(
            and_(
                OrdemCompra.empresa_id == usuario.empresa_id,
                OrdemCompra.status == "aguardando_aprovacao",
                OrdemCompra.valor_total <= alcada_suprimentos
            )
        )

        ordens_result = await db.execute(ordens_query)
        ordens = ordens_result.scalars().all()

        for ordem in ordens:
            aprovacoes_pendentes.append({
                "tipo": "ordem_compra",
                "id": ordem.id,
                "numero": ordem.numero,
                "descricao": f"Ordem de Compra #{ordem.numero}",
                "valor": float(ordem.valor_total),
                "solicitante_id": ordem.solicitante_id,
                "data_solicitacao": ordem.created_at,
                "prioridade": "normal"
            })

    # Could add other approval types here (contracts, expenses, etc.)

    return {
        "total_pendentes": len(aprovacoes_pendentes),
        "aprovacoes": aprovacoes_pendentes
    }


@router.post("/aprovar-lote")
async def aprovar_lote(
    aprovador_id: UUID,
    aprovacoes: List[Dict],  # [{"tipo": "ordem_compra", "id": "uuid"}]
    db: AsyncSession = Depends(get_db),
):
    """Approve multiple items in batch."""
    resultados = []

    for item in aprovacoes:
        try:
            if item["tipo"] == "ordem_compra":
                # Approve purchase order
                ordem_result = await db.execute(
                    select(OrdemCompra).where(OrdemCompra.id == item["id"])
                )
                ordem = ordem_result.scalar_one_or_none()

                if ordem and ordem.status == "aguardando_aprovacao":
                    # Get approver info
                    user_result = await db.execute(
                        select(Usuario).where(Usuario.id == aprovador_id)
                    )
                    usuario = user_result.scalar_one_or_none()

                    if not ordem.aprovadores:
                        ordem.aprovadores = []

                    ordem.aprovadores.append({
                        "usuario_id": str(aprovador_id),
                        "nome": usuario.nome if usuario else "Unknown",
                        "aprovado_em": str(date.today()),
                        "nivel": 1
                    })

                    ordem.status = "aprovada"

                    resultados.append({
                        "tipo": item["tipo"],
                        "id": item["id"],
                        "status": "aprovado"
                    })
                else:
                    resultados.append({
                        "tipo": item["tipo"],
                        "id": item["id"],
                        "status": "erro",
                        "mensagem": "Item not found or not pending"
                    })

        except Exception as e:
            resultados.append({
                "tipo": item.get("tipo"),
                "id": item.get("id"),
                "status": "erro",
                "mensagem": str(e)
            })

    await db.commit()

    return {
        "total_processados": len(resultados),
        "aprovados": sum(1 for r in resultados if r["status"] == "aprovado"),
        "erros": sum(1 for r in resultados if r["status"] == "erro"),
        "resultados": resultados
    }


@router.get("/historico/{usuario_id}")
async def get_historico_aprovacoes(
    usuario_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get approval history for a user."""
    # Get all orders approved by this user
    query = select(OrdemCompra).where(
        OrdemCompra.aprovadores.contains([{"usuario_id": str(usuario_id)}])
    )

    result = await db.execute(query)
    ordens = result.scalars().all()

    historico = []
    for ordem in ordens:
        if ordem.aprovadores:
            for aprovacao in ordem.aprovadores:
                if aprovacao.get("usuario_id") == str(usuario_id):
                    historico.append({
                        "tipo": "ordem_compra",
                        "id": ordem.id,
                        "numero": ordem.numero,
                        "valor": float(ordem.valor_total),
                        "data_aprovacao": aprovacao.get("aprovado_em"),
                        "status_atual": ordem.status
                    })

    # Sort by approval date
    historico.sort(key=lambda x: x.get("data_aprovacao", ""), reverse=True)

    return historico