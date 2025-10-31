"""
Centros de Custo router.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database.connection import get_db

router = APIRouter()


@router.get("/")
async def list_cost_centers(db: AsyncSession = Depends(get_db)):
    """List cost centers."""
    return {"message": "Cost centers endpoint - to be implemented"}