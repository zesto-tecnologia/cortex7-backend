"""
Prazos e Alertas (Deadlines and Alerts) router.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional
from datetime import date, timedelta
from uuid import UUID

from shared.database.connection import get_db
from shared.models.legal import Contract, Lawsuit

router = APIRouter()


@router.get("/all/{company_id}")
async def get_all_deadlines(
    company_id: UUID,
    days_limit: int = 90,
    db: AsyncSession = Depends(get_db),
):
    """Get all deadlines and important dates."""
    deadline_date = date.today() + timedelta(days=days_limit)
    deadlines = []

    # Contract deadlines
    contracts_query = select(Contract).where(
        and_(
            Contract.company_id == company_id,
            Contract.status == "active",
            Contract.end_date != None,
            Contract.end_date <= deadline_date
        )
    )
    contracts_result = await db.execute(contracts_query)
    contracts = contracts_result.scalars().all()

    for contract in contracts:
        days_remaining = (contract.end_date - date.today()).days

        deadlines.append({
            "type": "contract_expiration",
            "entidade_id": contract.id,
            "description": f"Contract expiration: {contract.opposing_party}",
            "date": contract.end_date,
            "days_remaining": days_remaining,
            "priority": "high" if days_remaining <= 15 else "medium",
            "auto_renewal": contract.auto_renewal
        })

        # Contract critical deadlines
        if contract.important_dates:
            for deadline in contract.important_dates:
                deadline_date = date.fromisoformat(deadline["date"])
                days_remaining = (deadline_date - date.today()).days
                deadlines.append({
                    "type": "important_date",
                    "entity_id": contract.id,
                    "description": deadline["description"],
                    "date": deadline_date,
                    "days_remaining": days_remaining,
                    "priority": "high" if days_remaining <= 7 else "medium",
                    "notified": deadline.get("notified", False)
                })

    # Legal process deadlines
    lawsuits_query = select(Lawsuit).where(
        and_(
            Lawsuit.company_id == company_id,
            Lawsuit.status == "active",
            Lawsuit.next_action != None,
            Lawsuit.next_action <= deadline_date
        )
    )
    lawsuits_result = await db.execute(lawsuits_query)
    lawsuits = lawsuits_result.scalars().all()

    for lawsuit in lawsuits:
        days_remaining = (lawsuit.next_action - date.today()).days

        deadlines.append({
            "type": "lawsuit_action",
            "entity_id": lawsuit.id,
            "description": lawsuit.next_action_description or f"Lawsuit action: {lawsuit.lawsuit_number}",
            "date": lawsuit.next_action,
            "days_remaining": days_remaining,
            "priority": "critical" if days_remaining <= 3 else "high" if days_remaining <= 7 else "medium",
            "risk": lawsuit.risk
        })

    # Sort by date
    deadlines.sort(key=lambda x: x["date"])

    return deadlines


@router.get("/critical/{company_id}")
async def get_critical_deadlines(
    company_id: UUID,
):
    """Get critical deadlines (next 7 days)."""
    deadlines = await get_all_deadlines(company_id, days_limit=7)

    # Filter only high priority
    critical_deadlines = [
        d for d in deadlines
        if d["priority"] in ["critical", "high"]
    ]

    return {
        "total_critical": len(critical_deadlines),
        "deadlines": critical_deadlines
    }


@router.get("/calendar/{company_id}")
async def get_deadline_calendar(
    company_id: UUID,
    year: int = 2025,
    month: Optional[int] = None,
):
    """Get deadline calendar."""
    import calendar

    # Define date range
    if month:
        start_date = date(year, month, 1)
        end_date = date(year, month, calendar.monthrange(year, month)[1])
    else:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

    # Get all deadlines for the period
    deadlines = await get_all_deadlines(company_id, days_limit=365)

    # Filter by date range
    calendar = {}
    for deadline in deadlines:
        if start_date <= deadline["date"] <= end_date:
            date_str = str(deadline["date"])
            if date_str not in calendar:
                calendar[date_str] = []
            calendar[date_str].append(deadline)

    return calendar


@router.post("/mark-notified/{company_id}")
async def mark_deadline_notified(
    company_id: UUID,
    entity_type: str,  # "contract" or "lawsuit"
    entity_id: UUID,
    deadline_description: str,
    db: AsyncSession = Depends(get_db),
):
    """Mark a deadline as notified."""
    if entity_type == "contract":
        result = await db.execute(
            select(Contract).where(
                and_(
                    Contract.id == entity_id,
                    Contract.company_id == company_id
                )
            )
        )
        contract = result.scalar_one_or_none()

        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")

        if contract.important_dates:
            for deadline in contract.important_dates:
                if deadline["description"] == deadline_description:
                    deadline["notified"] = True
                    break

        await db.commit()
        return {"message": "Deadline marked as notified"}

    elif entity_type == "lawsuit":
        result = await db.execute(
            select(Lawsuit).where(
                and_(
                    Lawsuit.id == entity_id,
                    Lawsuit.company_id == company_id
                )
            )
        )
        lawsuit = result.scalar_one_or_none()

        if not lawsuit:
            raise HTTPException(status_code=404, detail="Lawsuit not found")

        if lawsuit.important_dates:
            for deadline in lawsuit.important_dates:
                if deadline["description"] == deadline_description:
                    deadline["notified"] = True
                    break

        await db.commit()