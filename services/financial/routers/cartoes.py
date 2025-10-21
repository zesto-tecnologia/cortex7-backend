"""
Cartões Corporativos router.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database.connection import get_db

router = APIRouter()


@router.get("/")
async def list_cartoes(db: AsyncSession = Depends(get_db)):
    """List corporate cards."""
    return {"message": "Cartões endpoint - to be implemented"}


@router.get("/{cartao_id}/faturas")
async def list_faturas_cartao(cartao_id: str, db: AsyncSession = Depends(get_db)):
    """List card invoices."""
    return {"message": "Faturas endpoint - to be implemented"}


@router.get("/{cartao_id}/lancamentos")
async def list_lancamentos_cartao(cartao_id: str, db: AsyncSession = Depends(get_db)):
    """List card transactions."""
    return {"message": "Lançamentos endpoint - to be implemented"}