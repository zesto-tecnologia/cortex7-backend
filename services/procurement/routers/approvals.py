"""
Approvals workflow router.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Dict
from datetime import date
from uuid import UUID

from shared.database.connection import get_db
from shared.models.procurement import PurchaseOrder
from shared.models.user import UserProfile

router = APIRouter()


@router.get("/workflow-config")
async def get_workflow_config():
    """Get approval workflow configuration."""
    return {
        "levels": [
            {
                "level": 1,
                "name": "Supervisor",
                "min_limit": 0,
                "max_limit": 10000,
                "authority_required": "supervisor"
            },
            {
                "level": 2,
                "name": "Manager",
                "min_limit": 10001,
                "max_limit": 50000,
                "authority_required": "manager"
            },
            {
                "level": 3,
                "name": "Director",
                "min_limit": 50001,
                "max_limit": 200000,
                "authority_required": "director"
            },
            {
                "level": 4,
                "name": "President",
                "min_limit": 200001,
                "max_limit": None,
                "authority_required": "president"
            }
        ],
        "rules": [
            "Orders above $10,000 require 2 approvals",
            "Orders above $50,000 require director approval",
            "Orders above $200,000 require president approval",
            "Emergency purchases can skip one level with justification"
        ]
    }


@router.get("/pending/{user_id}")
async def get_pending_approvals(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all pending approvals for a user."""
    # Get user
    user_result = await db.execute(
        select(UserProfile).where(UserProfile.id == user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    pending_approvals = []

    # Purchase Orders
    procurement_authority = user.authorities.get("procurement", 0) if user.authorities else 0

    if procurement_authority > 0:
        orders_query = select(PurchaseOrder).where(
            and_(
                PurchaseOrder.company_id == user.company_id,
                PurchaseOrder.status == "awaiting_approval",
                PurchaseOrder.total_value <= procurement_authority
            )
        )

        orders_result = await db.execute(orders_query)
        orders = orders_result.scalars().all()

        for order in orders:
            pending_approvals.append({
                "type": "purchase_order",
                "id": order.id,
                "number": order.number,
                "description": f"Purchase Order #{order.number}",
                "value": float(order.total_value),
                "requester_id": order.requester_id,
                "request_date": order.created_at,
                "priority": "normal"
            })

    # Could add other approval types here (contracts, expenses, etc.)

    return {
        "total_pending": len(pending_approvals),
        "approvals": pending_approvals
    }


@router.post("/approve-batch")
async def approve_batch(
    approver_id: UUID,
    approvals: List[Dict],  # [{"type": "purchase_order", "id": "uuid"}]
    db: AsyncSession = Depends(get_db),
):
    """Approve multiple items in batch."""
    results = []

    for item in approvals:
        try:
            if item["type"] == "purchase_order":
                # Approve purchase order
                order_result = await db.execute(
                    select(PurchaseOrder).where(PurchaseOrder.id == item["id"])
                )
                order = order_result.scalar_one_or_none()

                if order and order.status == "awaiting_approval":
                    # Get approver info
                    user_result = await db.execute(
                        select(UserProfile).where(UserProfile.id == approver_id)
                    )
                    user = user_result.scalar_one_or_none()

                    if not order.approvers:
                        order.approvers = []

                    order.approvers.append({
                        "user_id": str(approver_id),
                        "name": user.name if user else "Unknown",
                        "approved_at": str(date.today()),
                        "level": 1
                    })

                    order.status = "approved"

                    results.append({
                        "type": item["type"],
                        "id": item["id"],
                        "status": "approved"
                    })
                else:
                    results.append({
                        "type": item["type"],
                        "id": item["id"],
                        "status": "error",
                        "message": "Item not found or not pending"
                    })

        except Exception as e:
            results.append({
                "type": item.get("type"),
                "id": item.get("id"),
                "status": "error",
                "message": str(e)
            })

    await db.commit()

    return {
        "total_processed": len(results),
        "approved": sum(1 for r in results if r["status"] == "approved"),
        "errors": sum(1 for r in results if r["status"] == "error"),
        "results": results
    }


@router.get("/history/{user_id}")
async def get_approval_history(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get approval history for a user."""
    # Get all orders approved by this user
    query = select(PurchaseOrder).where(
        PurchaseOrder.approvers.contains([{"user_id": str(user_id)}])
    )

    result = await db.execute(query)
    orders = result.scalars().all()

    history = []
    for order in orders:
        if order.approvers:
            for approval in order.approvers:
                if approval.get("user_id") == str(user_id):
                    history.append({
                        "type": "purchase_order",
                        "id": order.id,
                        "number": order.number,
                        "value": float(order.total_value),
                        "approval_date": approval.get("approved_at"),
                        "current_status": order.status
                    })

    # Sort by approval date
    history.sort(key=lambda x: x.get("approval_date", ""), reverse=True)

    return history