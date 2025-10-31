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
from shared.models.procurement import PurchaseOrder
from shared.models.financial import Supplier

router = APIRouter()


@router.get("/spend-overview/{company_id}")
async def get_spend_overview(
    company_id: UUID,
    period_days: int = 30,
    db: AsyncSession = Depends(get_db),
):
    """Get spending overview for the company."""
    start_date = date.today() - timedelta(days=period_days)

    # Total spend
    query = select(
        func.count(PurchaseOrder.id).label("total_orders"),
        func.sum(PurchaseOrder.total_amount).label("total_amount"),
        func.avg(PurchaseOrder.total_amount).label("average_value")
    ).where(
        and_(
            PurchaseOrder.company_id == company_id,
            PurchaseOrder.created_at >= start_date,
            PurchaseOrder.status.in_(["approved", "order_issued", "received"])
        )
    )

    result = await db.execute(query)
    stats = result.fetchone()

    # By status
    status_query = select(
        PurchaseOrder.status,
        func.count(PurchaseOrder.id).label("quantity"),
        func.sum(PurchaseOrder.total_amount).label("amount")
    ).where(
        and_(
            PurchaseOrder.company_id == company_id,
            PurchaseOrder.created_at >= start_date
        )
    ).group_by(PurchaseOrder.status)

    status_result = await db.execute(status_query)
    status_breakdown = status_result.fetchall()

    return {
        "period_days": period_days,
        "total_orders": stats.total_orders or 0,
        "total_amount": float(stats.total_amount) if stats.total_amount else 0,
        "average_value": float(stats.average_value) if stats.average_value else 0,
        "by_status": [
            {
                "status": row.status,
                "quantity": row.quantity,
                "amount": float(row.amount) if row.amount else 0
            }
            for row in status_breakdown
        ]
    }


@router.get("/top-suppliers/{company_id}")
async def get_top_suppliers(
    company_id: UUID,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get top suppliers by spend."""
    query = select(
        PurchaseOrder.supplier_id,
        Supplier.company_name,
        Supplier.tax_id,
        func.count(PurchaseOrder.id).label("total_orders"),
        func.sum(PurchaseOrder.total_amount).label("total_amount")
    ).join(
        Supplier,
        PurchaseOrder.supplier_id == Supplier.id
    ).where(
        and_(
            PurchaseOrder.company_id == company_id,
            PurchaseOrder.status.in_(["approved", "order_issued", "received"])
        )
    ).group_by(
        PurchaseOrder.supplier_id,
        Supplier.company_name,
        Supplier.tax_id
    ).order_by(
        func.sum(PurchaseOrder.total_amount).desc()
    ).limit(limit)

    result = await db.execute(query)
    suppliers = result.fetchall()

    return [
        {
            "supplier_id": s.supplier_id,
            "company_name": s.company_name,
            "tax_id": s.tax_id,
            "total_orders": s.total_orders,
            "total_amount": float(s.total_amount) if s.total_amount else 0
        }
        for s in suppliers
    ]


@router.get("/spend-by-category/{company_id}")
async def get_spend_by_category(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get spending breakdown by category."""
    query = select(
        PurchaseOrder.cost_center,
        func.count(PurchaseOrder.id).label("quantity"),
        func.sum(PurchaseOrder.total_amount).label("amount")
    ).where(
        and_(
            PurchaseOrder.company_id == company_id,
            PurchaseOrder.status.in_(["approved", "order_issued", "received"])
        )
    ).group_by(PurchaseOrder.cost_center)

    result = await db.execute(query)
    categories = result.fetchall()

    total_spend = sum(float(c.amount) if c.amount else 0 for c in categories)

    return [
        {
            "category": c.cost_center or "Uncategorized",
            "quantity": c.quantity,
            "amount": float(c.amount) if c.amount else 0,
            "percentage": (float(c.amount) / total_spend * 100) if c.amount and total_spend > 0 else 0
        }
        for c in categories
    ]


@router.get("/approval-metrics/{company_id}")
async def get_approval_metrics(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get approval process metrics."""
    # Average approval time
    approved = await db.execute(
        select(PurchaseOrder).where(
            and_(
                PurchaseOrder.company_id == company_id,
                PurchaseOrder.status == "approved"
            )
        )
    )

    approved_orders = approved.scalars().all()

    approval_times = []
    for order in approved_orders:
        if order.approvers and len(order.approvers) > 0:
            first_approval = order.approvers[0].get("approved_at")
            if first_approval:
                approval_date = date.fromisoformat(first_approval)
                days_to_approve = (approval_date - order.created_at.date()).days
                approval_times.append(days_to_approve)

    # Rejection rate
    total_query = select(func.count(PurchaseOrder.id)).where(
        PurchaseOrder.company_id == company_id
    )
    total_result = await db.execute(total_query)
    total_orders = total_result.scalar() or 0

    cancelled_query = select(func.count(PurchaseOrder.id)).where(
        and_(
            PurchaseOrder.company_id == company_id,
            PurchaseOrder.status == "cancelled"
        )
    )
    cancelled_result = await db.execute(cancelled_query)
    total_cancelled = cancelled_result.scalar() or 0

    return {
        "average_approval_time_days": sum(approval_times) / len(approval_times) if approval_times else 0,
        "minimum_time_days": min(approval_times) if approval_times else 0,
        "maximum_time_days": max(approval_times) if approval_times else 0,
        "rejection_rate": (total_cancelled / total_orders * 100) if total_orders > 0 else 0,
        "total_approved": len(approved_orders),
        "total_rejected": total_cancelled
    }


@router.get("/savings-opportunities/{company_id}")
async def get_savings_opportunities(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Identify potential savings opportunities."""
    # Get duplicate orders (same items from different suppliers)
    query = select(PurchaseOrder).where(
        and_(
            PurchaseOrder.company_id == company_id,
            PurchaseOrder.status.in_(["approved", "order_issued", "received"])
        )
    )

    result = await db.execute(query)
    orders = result.scalars().all()

    # Analyze items for price variations
    item_prices = {}
    for order in orders:
        if order.items:
            for item in order.items:
                description = item.get("description", "")
                unit_amount = item.get("unit_amount", 0)

                if description not in item_prices:
                    item_prices[description] = []

                item_prices[description].append({
                    "supplier_id": order.supplier_id,
                    "amount": unit_amount,
                    "date": order.created_at
                })

    # Find items with significant price variations
    opportunities = []
    for item, prices in item_prices.items():
        if len(prices) > 1:
            values = [p["amount"] for p in prices]
            min_amount = min(values)
            max_amount = max(values)

            if max_amount > min_amount * 1.1:  # More than 10% difference
                potential_savings = (max_amount - min_amount) / max_amount * 100

                opportunities.append({
                    "item": item,
                    "lowest_amount": min_amount,
                    "highest_amount": max_amount,
                    "potential_savings_percentage": potential_savings,
                    "suppliers_count": len(set(p["supplier_id"] for p in prices))
                })

    # Sort by potential savings
    opportunities.sort(key=lambda x: x["potential_savings_percentage"], reverse=True)

    return {
        "total_opportunities": len(opportunities),
        "opportunities": opportunities[:10]  # Top 10 opportunities
    }