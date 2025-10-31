"""
Procurement microservice main application.
Handles purchase orders, supplier management, and procurement workflows.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config.settings import settings

# Create FastAPI app
app = FastAPI(
    title="Procurement Service",
    description="Procurement and supplier management microservice",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Procurement Service",
        "version": "1.0.0",
        "status": "operational",
        "features": [
            "purchase_orders",
            "supplier_management",
            "approval_workflows",
            "spend_analytics"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Import routers
from services.procurement.routers import purchase_orders, approvals, analytics

# Include routers
app.include_router(purchase_orders.router, prefix="/purchase-orders", tags=["Purchase Orders"])
app.include_router(approvals.router, prefix="/approvals", tags=["Approvals"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])


if __name__ == "__main__":
    port = int(settings.procurement_service_port)
    uvicorn.run("services.procurement.main:app", host="0.0.0.0", port=port, reload=True)