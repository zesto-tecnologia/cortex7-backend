"""
Cartões Corporativos router.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database.connection import get_db

router = APIRouter()


@router.get("/")
async def list_cards(db: AsyncSession = Depends(get_db)):
    """List corporate cards."""
    return {"message": "Cards endpoint - to be implemented"}


@router.get("/{card_id}/invoices")
async def list_invoices_card(card_id: str, db: AsyncSession = Depends(get_db)):
    """List card invoices."""
    return {"message": "Invoices endpoint - to be implemented"}


@router.get("/{card_id}/transactions")
async def list_transactions_card(card_id: str, db: AsyncSession = Depends(get_db)):
    """List card transactions."""
    return {"message": "Transactions endpoint - to be implemented"}