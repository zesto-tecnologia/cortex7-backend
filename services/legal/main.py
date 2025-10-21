"""
Legal microservice main application.
Handles contracts, legal processes, and compliance.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.config.settings import settings
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="Legal Service",
    description="Legal operations and contract management microservice",
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
        "service": "Legal Service",
        "version": "1.0.0",
        "status": "operational",
        "features": [
            "contract_management",
            "legal_processes",
            "compliance_tracking",
            "deadline_monitoring"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Import routers
from services.legal.routers import contratos, processos, prazos

# Include routers
app.include_router(contratos.router, prefix="/contratos", tags=["Contratos"])
app.include_router(processos.router, prefix="/processos", tags=["Processos Jurídicos"])
app.include_router(prazos.router, prefix="/prazos", tags=["Prazos e Alertas"])


if __name__ == "__main__":
    port = int(settings.legal_service_port)
    uvicorn.run(app, host="0.0.0.0", port=port)