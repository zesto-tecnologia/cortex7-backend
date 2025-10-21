"""
Financial microservice main application.
"""

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database.connection import get_db
from shared.config.settings import settings
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="Financial Service",
    description="Microservice for financial operations",
    version="1.0.0",
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Financial Service",
        "version": "1.0.0",
        "status": "operational",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Import routers
from services.financial.routers import (
    contas_pagar,
    cartoes,
    fornecedores,
    centros_custo,
)

# Include routers
app.include_router(contas_pagar.router, prefix="/contas-pagar", tags=["Contas a Pagar"])
app.include_router(cartoes.router, prefix="/cartoes", tags=["Cartões Corporativos"])
app.include_router(fornecedores.router, prefix="/fornecedores", tags=["Fornecedores"])
app.include_router(centros_custo.router, prefix="/centros-custo", tags=["Centros de Custo"])


if __name__ == "__main__":
    port = int(settings.financial_service_port)
    uvicorn.run(app, host="0.0.0.0", port=port)