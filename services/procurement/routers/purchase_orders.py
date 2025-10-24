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
from shared.models.procurement import PurchaseOrder
from shared.models.user import UserProfile
from services.procurement.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderWithApprovals,
    PurchaseOrderItem,
)

router = APIRouter()


@router.get("/", response_model=List[PurchaseOrderResponse])
async def list_purchase_orders(
    company_id: UUID,
    status: Optional[str] = None,
    supplier_id: Optional[UUID] = None,
    requester_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """List purchase orders with filters."""
    query = select(PurchaseOrder).where(PurchaseOrder.company_id == company_id)

    if status:
        query = query.where(PurchaseOrder.status == status)

    if supplier_id:
        query = query.where(PurchaseOrder.supplier_id == supplier_id)

    if requester_id:
        query = query.where(PurchaseOrder.requester_id == requester_id)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/pending-approval")
async def get_pending_orders(
    company_id: UUID,
    approver_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get purchase orders pending approval for a specific approver."""
    # Get user's approval limit
    user_result = await db.execute(
        select(UserProfile).where(UserProfile.id == approver_id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Approver not found")

    procurement_authority = user.authorities.get("procurement", 0) if user.authorities else 0

    # Get orders within approval limit
    query = select(PurchaseOrder).where(
        and_(
            PurchaseOrder.company_id == company_id,
            PurchaseOrder.status == "awaiting_approval",
            PurchaseOrder.total_value <= procurement_authority
        )
    )

    result = await db.execute(query)
    orders = result.scalars().all()

    return [
        {
            "id": o.id,
            "number": o.number,
            "supplier_id": o.supplier_id,
            "total_value": float(o.total_value),
            "items_count": len(o.items) if o.items else 0,
            "created_at": o.created_at,
            "can_approve": float(o.total_value) <= procurement_authority
        }
        for o in orders
    ]


@router.get("/{order_id}", response_model=PurchaseOrderWithApprovals)
async def get_ordem_compra(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific purchase order with approval details."""
    from sqlalchemy.orm import selectinload

    query = select(PurchaseOrder).options(
        selectinload(PurchaseOrder.solicitante),
        selectinload(PurchaseOrder.supplier)
    ).where(PurchaseOrder.id == order_id)

    result = await db.execute(query)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    return order


@router.post("/", response_model=PurchaseOrderResponse)
async def create_ordem_compra(
    order: PurchaseOrderCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new purchase order."""
    import random
    import string

    # Generate unique order number
    number = ''.join(random.choices(string.digits, k=10))

    # Calculate total from items
    total_value = sum(
        item.quantity * item.unit_value
        for item in order.items
    )

    db_ordem = PurchaseOrder(
        **order.dict(exclude={'items'}),
        number=number,
        total_value=total_value,
        items=[item.dict() for item in order.items]
    )

    db.add(db_ordem)
    await db.commit()
    await db.refresh(db_ordem)
    return db_ordem


@router.put("/{order_id}", response_model=PurchaseOrderResponse)
async def update_ordem_compra(
    order_id: UUID,
    ordem_update: PurchaseOrderUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a purchase order."""
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    if order.status not in ["rascunho", "awaiting_approval"]:
        raise HTTPException(
            status_code=400,
            detail="Can only update draft or pending approval orders"
        )

    # Update fields
    for field, value in ordem_update.dict(exclude_unset=True, exclude={'items'}).items():
        setattr(order, field, value)

    # Update items if provided
    if ordem_update.items:
        order.items = [item.dict() for item in ordem_update.items]
        # Recalculate total
        order.total_value = sum(
            item["quantity"] * item["unit_value"]
            for item in order.items
        )

    await db.commit()
    await db.refresh(order)
    return order


@router.post("/{order_id}/aprovar")
async def approve_order(
    order_id: UUID,
    approver_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Approve a purchase order."""
    # Get order
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    if order.status != "awaiting_approval":
        raise HTTPException(
            status_code=400,
            detail="Order is not pending approval"
        )

    # Get approver
    user_result = await db.execute(
        select(UserProfile).where(UserProfile.id == approver_id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Approver not found")

    # Check approval limit
    procurement_authority = user.authorities.get("procurement", 0) if user.authorities else 0

    if float(order.total_value) > procurement_authority:
        raise HTTPException(
            status_code=403,
            detail=f"Order value exceeds approval limit of {procurement_authority}"
        )

    # Record approval
    if not order.approvers:
        order.approvers = []

    order.approvers.append({
        "user_id": str(approver_id),
        "name": user.name,
        "approved_at": str(date.today()),
        "level": 1,
        "approved_value": float(order.total_value)
    })

    order.status = "approved"

    await db.commit()

    return {"message": "Purchase order approved successfully"}


@router.post("/{order_id}/rejeitar")
async def reject_order(
    order_id: UUID,
    motivo: str,
    rejeitado_por: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Reject a purchase order."""
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    if order.status != "awaiting_approval":
        raise HTTPException(
            status_code=400,
            detail="Order is not pending approval"
        )

    order.status = "cancelled"

    if not order.metadata:
        order.metadata = {}

    order.metadata["rejeicao"] = {
        "rejeitado_por": str(rejeitado_por),
        "motivo": motivo,
        "date": str(date.today())
    }

    await db.commit()

    return {"message": "Purchase order rejected"}


@router.post("/{order_id}/emitir")
async def issue_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Issue a purchase order to supplier."""
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    if order.status != "approved":
        raise HTTPException(
            status_code=400,
            detail="Order must be approved before issuing"
        )

    order.status = "order_issued"

    if not order.metadata:
        order.metadata = {}

    order.metadata["emissao"] = {
        "emitido_em": str(date.today())
    }

    await db.commit()

    return {"message": "Purchase order issued to supplier"}


@router.post("/{order_id}/receive")
async def receive_order(
    order_id: UUID,
    received_items: List[PurchaseOrderItem],
    db: AsyncSession = Depends(get_db),
):
    """Mark purchase order items as received."""
    result = await db.execute(
        select(PurchaseOrder).where(PurchaseOrder.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    if order.status != "order_issued":
        raise HTTPException(
            status_code=400,
            detail="Order must be issued before receiving"
        )

    order.status = "received"

    if not order.metadata:
        order.metadata = {}

    order.metadata["receipt"] = {
        "received_at": str(date.today()),
        "received_items": received_items
    }

    await db.commit()

    return {"message": "Purchase order marked as received"}