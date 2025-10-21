"""
Ordens de Compra (Purchase Orders) router.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional, Dict
from datetime import date
from uuid import UUID

from shared.database.connection import get_db
from shared.models.suprimentos import OrdemCompra
from shared.models.usuario import Usuario
from services.procurement.schemas.ordem_compra import (
    OrdemCompraCreate,
    OrdemCompraUpdate,
    OrdemCompraResponse,
    OrdemCompraWithAprovacoes,
    ItemOrdemCompra,
)

router = APIRouter()


@router.get("/", response_model=List[OrdemCompraResponse])
async def list_ordens_compra(
    empresa_id: UUID,
    status: Optional[str] = None,
    fornecedor_id: Optional[UUID] = None,
    solicitante_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """List purchase orders with filters."""
    query = select(OrdemCompra).where(OrdemCompra.empresa_id == empresa_id)

    if status:
        query = query.where(OrdemCompra.status == status)

    if fornecedor_id:
        query = query.where(OrdemCompra.fornecedor_id == fornecedor_id)

    if solicitante_id:
        query = query.where(OrdemCompra.solicitante_id == solicitante_id)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/pendentes-aprovacao")
async def get_ordens_pendentes(
    empresa_id: UUID,
    aprovador_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get purchase orders pending approval for a specific approver."""
    # Get user's approval limit
    user_result = await db.execute(
        select(Usuario).where(Usuario.id == aprovador_id)
    )
    usuario = user_result.scalar_one_or_none()

    if not usuario:
        raise HTTPException(status_code=404, detail="Approver not found")

    alcada_suprimentos = usuario.alcadas.get("suprimentos", 0) if usuario.alcadas else 0

    # Get orders within approval limit
    query = select(OrdemCompra).where(
        and_(
            OrdemCompra.empresa_id == empresa_id,
            OrdemCompra.status == "aguardando_aprovacao",
            OrdemCompra.valor_total <= alcada_suprimentos
        )
    )

    result = await db.execute(query)
    ordens = result.scalars().all()

    return [
        {
            "id": o.id,
            "numero": o.numero,
            "fornecedor_id": o.fornecedor_id,
            "valor_total": float(o.valor_total),
            "itens_count": len(o.itens) if o.itens else 0,
            "created_at": o.created_at,
            "pode_aprovar": float(o.valor_total) <= alcada_suprimentos
        }
        for o in ordens
    ]


@router.get("/{ordem_id}", response_model=OrdemCompraWithAprovacoes)
async def get_ordem_compra(
    ordem_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific purchase order with approval details."""
    from sqlalchemy.orm import selectinload

    query = select(OrdemCompra).options(
        selectinload(OrdemCompra.solicitante),
        selectinload(OrdemCompra.fornecedor)
    ).where(OrdemCompra.id == ordem_id)

    result = await db.execute(query)
    ordem = result.scalar_one_or_none()

    if not ordem:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    return ordem


@router.post("/", response_model=OrdemCompraResponse)
async def create_ordem_compra(
    ordem: OrdemCompraCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new purchase order."""
    import random
    import string

    # Generate unique order number
    numero = ''.join(random.choices(string.digits, k=10))

    # Calculate total from items
    valor_total = sum(
        item.quantidade * item.valor_unitario
        for item in ordem.itens
    )

    db_ordem = OrdemCompra(
        **ordem.dict(exclude={'itens'}),
        numero=numero,
        valor_total=valor_total,
        itens=[item.dict() for item in ordem.itens]
    )

    db.add(db_ordem)
    await db.commit()
    await db.refresh(db_ordem)
    return db_ordem


@router.put("/{ordem_id}", response_model=OrdemCompraResponse)
async def update_ordem_compra(
    ordem_id: UUID,
    ordem_update: OrdemCompraUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a purchase order."""
    result = await db.execute(
        select(OrdemCompra).where(OrdemCompra.id == ordem_id)
    )
    ordem = result.scalar_one_or_none()

    if not ordem:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    if ordem.status not in ["rascunho", "aguardando_aprovacao"]:
        raise HTTPException(
            status_code=400,
            detail="Can only update draft or pending approval orders"
        )

    # Update fields
    for field, value in ordem_update.dict(exclude_unset=True, exclude={'itens'}).items():
        setattr(ordem, field, value)

    # Update items if provided
    if ordem_update.itens:
        ordem.itens = [item.dict() for item in ordem_update.itens]
        # Recalculate total
        ordem.valor_total = sum(
            item["quantidade"] * item["valor_unitario"]
            for item in ordem.itens
        )

    await db.commit()
    await db.refresh(ordem)
    return ordem


@router.post("/{ordem_id}/aprovar")
async def aprovar_ordem(
    ordem_id: UUID,
    aprovador_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Approve a purchase order."""
    # Get order
    result = await db.execute(
        select(OrdemCompra).where(OrdemCompra.id == ordem_id)
    )
    ordem = result.scalar_one_or_none()

    if not ordem:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    if ordem.status != "aguardando_aprovacao":
        raise HTTPException(
            status_code=400,
            detail="Order is not pending approval"
        )

    # Get approver
    user_result = await db.execute(
        select(Usuario).where(Usuario.id == aprovador_id)
    )
    usuario = user_result.scalar_one_or_none()

    if not usuario:
        raise HTTPException(status_code=404, detail="Approver not found")

    # Check approval limit
    alcada_suprimentos = usuario.alcadas.get("suprimentos", 0) if usuario.alcadas else 0

    if float(ordem.valor_total) > alcada_suprimentos:
        raise HTTPException(
            status_code=403,
            detail=f"Order value exceeds approval limit of {alcada_suprimentos}"
        )

    # Record approval
    if not ordem.aprovadores:
        ordem.aprovadores = []

    ordem.aprovadores.append({
        "usuario_id": str(aprovador_id),
        "nome": usuario.nome,
        "aprovado_em": str(date.today()),
        "nivel": 1,
        "valor_aprovado": float(ordem.valor_total)
    })

    ordem.status = "aprovada"

    await db.commit()

    return {"message": "Purchase order approved successfully"}


@router.post("/{ordem_id}/rejeitar")
async def rejeitar_ordem(
    ordem_id: UUID,
    motivo: str,
    rejeitado_por: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Reject a purchase order."""
    result = await db.execute(
        select(OrdemCompra).where(OrdemCompra.id == ordem_id)
    )
    ordem = result.scalar_one_or_none()

    if not ordem:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    if ordem.status != "aguardando_aprovacao":
        raise HTTPException(
            status_code=400,
            detail="Order is not pending approval"
        )

    ordem.status = "cancelada"

    if not ordem.metadata:
        ordem.metadata = {}

    ordem.metadata["rejeicao"] = {
        "rejeitado_por": str(rejeitado_por),
        "motivo": motivo,
        "data": str(date.today())
    }

    await db.commit()

    return {"message": "Purchase order rejected"}


@router.post("/{ordem_id}/emitir")
async def emitir_ordem(
    ordem_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Issue a purchase order to supplier."""
    result = await db.execute(
        select(OrdemCompra).where(OrdemCompra.id == ordem_id)
    )
    ordem = result.scalar_one_or_none()

    if not ordem:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    if ordem.status != "aprovada":
        raise HTTPException(
            status_code=400,
            detail="Order must be approved before issuing"
        )

    ordem.status = "pedido_emitido"

    if not ordem.metadata:
        ordem.metadata = {}

    ordem.metadata["emissao"] = {
        "emitido_em": str(date.today())
    }

    await db.commit()

    return {"message": "Purchase order issued to supplier"}


@router.post("/{ordem_id}/receber")
async def receber_ordem(
    ordem_id: UUID,
    itens_recebidos: List[Dict],
    db: AsyncSession = Depends(get_db),
):
    """Mark purchase order items as received."""
    result = await db.execute(
        select(OrdemCompra).where(OrdemCompra.id == ordem_id)
    )
    ordem = result.scalar_one_or_none()

    if not ordem:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    if ordem.status != "pedido_emitido":
        raise HTTPException(
            status_code=400,
            detail="Order must be issued before receiving"
        )

    ordem.status = "recebido"

    if not ordem.metadata:
        ordem.metadata = {}

    ordem.metadata["recebimento"] = {
        "recebido_em": str(date.today()),
        "itens": itens_recebidos
    }

    await db.commit()

    return {"message": "Purchase order marked as received"}