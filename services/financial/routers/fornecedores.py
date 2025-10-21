"""
Fornecedores router.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database.connection import get_db

router = APIRouter()


@router.get("/")
async def list_fornecedores(db: AsyncSession = Depends(get_db)):
    """List suppliers."""
    return {"message": "Fornecedores endpoint - to be implemented"}