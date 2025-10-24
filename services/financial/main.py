"""
Financial microservice main application.
"""

import uvicorn
from fastapi import FastAPI

from shared.config.settings import settings

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
    accounts_payable,
    cards,
    suppliers,
    cost_centers,
)

# Include routers
app.include_router(accounts_payable.router, prefix="/accounts-payable", tags=["Accounts Payable"])
app.include_router(cards.router, prefix="/cards", tags=["Corporate Cards"])
app.include_router(suppliers.router, prefix="/suppliers", tags=["Suppliers"])
app.include_router(cost_centers.router, prefix="/cost-centers", tags=["Cost Centers"])


if __name__ == "__main__":
    port = int(settings.financial_service_port)
    uvicorn.run("services.financial.main:app", host="0.0.0.0", port=port, reload=True)