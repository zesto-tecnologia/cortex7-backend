"""
Analytics router for procurement insights.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
from datetime import date, timedelta
from uuid import UUID

from shared.database.connection import get_db
from shared.models.suprimentos import OrdemCompra
from shared.models.financeiro import Fornecedor

router = APIRouter()


@router.get("/spend-overview/{empresa_id}")
async def get_spend_overview(
    empresa_id: UUID,
    periodo_dias: int = 30,
    db: AsyncSession = Depends(get_db),
):
    """Get spending overview for the company."""
    data_inicio = date.today() - timedelta(days=periodo_dias)

    # Total spend
    query = select(
        func.count(OrdemCompra.id).label("total_ordens"),
        func.sum(OrdemCompra.valor_total).label("valor_total"),
        func.avg(OrdemCompra.valor_total).label("valor_medio")
    ).where(
        and_(
            OrdemCompra.empresa_id == empresa_id,
            OrdemCompra.created_at >= data_inicio,
            OrdemCompra.status.in_(["aprovada", "pedido_emitido", "recebido"])
        )
    )

    result = await db.execute(query)
    stats = result.fetchone()

    # By status
    status_query = select(
        OrdemCompra.status,
        func.count(OrdemCompra.id).label("quantidade"),
        func.sum(OrdemCompra.valor_total).label("valor")
    ).where(
        and_(
            OrdemCompra.empresa_id == empresa_id,
            OrdemCompra.created_at >= data_inicio
        )
    ).group_by(OrdemCompra.status)

    status_result = await db.execute(status_query)
    status_breakdown = status_result.fetchall()

    return {
        "periodo_dias": periodo_dias,
        "total_ordens": stats.total_ordens or 0,
        "valor_total": float(stats.valor_total) if stats.valor_total else 0,
        "valor_medio": float(stats.valor_medio) if stats.valor_medio else 0,
        "por_status": [
            {
                "status": row.status,
                "quantidade": row.quantidade,
                "valor": float(row.valor) if row.valor else 0
            }
            for row in status_breakdown
        ]
    }


@router.get("/top-fornecedores/{empresa_id}")
async def get_top_fornecedores(
    empresa_id: UUID,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get top suppliers by spend."""
    query = select(
        OrdemCompra.fornecedor_id,
        Fornecedor.razao_social,
        Fornecedor.cnpj,
        func.count(OrdemCompra.id).label("total_ordens"),
        func.sum(OrdemCompra.valor_total).label("valor_total")
    ).join(
        Fornecedor,
        OrdemCompra.fornecedor_id == Fornecedor.id
    ).where(
        and_(
            OrdemCompra.empresa_id == empresa_id,
            OrdemCompra.status.in_(["aprovada", "pedido_emitido", "recebido"])
        )
    ).group_by(
        OrdemCompra.fornecedor_id,
        Fornecedor.razao_social,
        Fornecedor.cnpj
    ).order_by(
        func.sum(OrdemCompra.valor_total).desc()
    ).limit(limit)

    result = await db.execute(query)
    fornecedores = result.fetchall()

    return [
        {
            "fornecedor_id": f.fornecedor_id,
            "razao_social": f.razao_social,
            "cnpj": f.cnpj,
            "total_ordens": f.total_ordens,
            "valor_total": float(f.valor_total) if f.valor_total else 0
        }
        for f in fornecedores
    ]


@router.get("/spend-by-category/{empresa_id}")
async def get_spend_by_category(
    empresa_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get spending breakdown by category."""
    query = select(
        OrdemCompra.centro_custo,
        func.count(OrdemCompra.id).label("quantidade"),
        func.sum(OrdemCompra.valor_total).label("valor")
    ).where(
        and_(
            OrdemCompra.empresa_id == empresa_id,
            OrdemCompra.status.in_(["aprovada", "pedido_emitido", "recebido"])
        )
    ).group_by(OrdemCompra.centro_custo)

    result = await db.execute(query)
    categorias = result.fetchall()

    total_spend = sum(float(c.valor) if c.valor else 0 for c in categorias)

    return [
        {
            "categoria": c.centro_custo or "Não categorizado",
            "quantidade": c.quantidade,
            "valor": float(c.valor) if c.valor else 0,
            "percentual": (float(c.valor) / total_spend * 100) if c.valor and total_spend > 0 else 0
        }
        for c in categorias
    ]


@router.get("/approval-metrics/{empresa_id}")
async def get_approval_metrics(
    empresa_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get approval process metrics."""
    # Average approval time
    aprovadas = await db.execute(
        select(OrdemCompra).where(
            and_(
                OrdemCompra.empresa_id == empresa_id,
                OrdemCompra.status == "aprovada"
            )
        )
    )

    ordens_aprovadas = aprovadas.scalars().all()

    tempos_aprovacao = []
    for ordem in ordens_aprovadas:
        if ordem.aprovadores and len(ordem.aprovadores) > 0:
            primeira_aprovacao = ordem.aprovadores[0].get("aprovado_em")
            if primeira_aprovacao:
                data_aprovacao = date.fromisoformat(primeira_aprovacao)
                tempo_dias = (data_aprovacao - ordem.created_at.date()).days
                tempos_aprovacao.append(tempo_dias)

    # Rejection rate
    total_query = select(func.count(OrdemCompra.id)).where(
        OrdemCompra.empresa_id == empresa_id
    )
    total_result = await db.execute(total_query)
    total_ordens = total_result.scalar() or 0

    canceladas_query = select(func.count(OrdemCompra.id)).where(
        and_(
            OrdemCompra.empresa_id == empresa_id,
            OrdemCompra.status == "cancelada"
        )
    )
    canceladas_result = await db.execute(canceladas_query)
    total_canceladas = canceladas_result.scalar() or 0

    return {
        "tempo_medio_aprovacao_dias": sum(tempos_aprovacao) / len(tempos_aprovacao) if tempos_aprovacao else 0,
        "tempo_minimo_dias": min(tempos_aprovacao) if tempos_aprovacao else 0,
        "tempo_maximo_dias": max(tempos_aprovacao) if tempos_aprovacao else 0,
        "taxa_rejeicao": (total_canceladas / total_ordens * 100) if total_ordens > 0 else 0,
        "total_aprovadas": len(ordens_aprovadas),
        "total_rejeitadas": total_canceladas
    }


@router.get("/savings-opportunities/{empresa_id}")
async def get_savings_opportunities(
    empresa_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Identify potential savings opportunities."""
    # Get duplicate orders (same items from different suppliers)
    query = select(OrdemCompra).where(
        and_(
            OrdemCompra.empresa_id == empresa_id,
            OrdemCompra.status.in_(["aprovada", "pedido_emitido", "recebido"])
        )
    )

    result = await db.execute(query)
    ordens = result.scalars().all()

    # Analyze items for price variations
    item_prices = {}
    for ordem in ordens:
        if ordem.itens:
            for item in ordem.itens:
                descricao = item.get("descricao", "")
                valor_unit = item.get("valor_unitario", 0)

                if descricao not in item_prices:
                    item_prices[descricao] = []

                item_prices[descricao].append({
                    "fornecedor_id": ordem.fornecedor_id,
                    "valor": valor_unit,
                    "data": ordem.created_at
                })

    # Find items with significant price variations
    oportunidades = []
    for item, precos in item_prices.items():
        if len(precos) > 1:
            valores = [p["valor"] for p in precos]
            min_valor = min(valores)
            max_valor = max(valores)

            if max_valor > min_valor * 1.1:  # More than 10% difference
                economia_potencial = (max_valor - min_valor) / max_valor * 100

                oportunidades.append({
                    "item": item,
                    "menor_preco": min_valor,
                    "maior_preco": max_valor,
                    "economia_potencial_pct": economia_potencial,
                    "fornecedores_count": len(set(p["fornecedor_id"] for p in precos))
                })

    # Sort by potential savings
    oportunidades.sort(key=lambda x: x["economia_potencial_pct"], reverse=True)

    return {
        "total_oportunidades": len(oportunidades),
        "oportunidades": oportunidades[:10]  # Top 10 opportunities
    }