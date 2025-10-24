"""
Fornecedores router.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database.connection import get_db

router = APIRouter()


@router.get("/")
async def list_suppliers(db: AsyncSession = Depends(get_db)):
    """List suppliers."""
    return {"message": "Suppliers endpoint - to be implemented"}