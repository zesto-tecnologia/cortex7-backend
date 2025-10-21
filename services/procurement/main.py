"""
Procurement microservice main application.
Handles purchase orders, supplier management, and procurement workflows.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.config.settings import settings
import uvicorn

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
from services.procurement.routers import ordens_compra, aprovacoes, analytics

# Include routers
app.include_router(ordens_compra.router, prefix="/ordens-compra", tags=["Ordens de Compra"])
app.include_router(aprovacoes.router, prefix="/aprovacoes", tags=["Aprovações"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])


if __name__ == "__main__":
    port = int(settings.procurement_service_port)
    uvicorn.run(app, host="0.0.0.0", port=port)