"""
Legal microservice main application.
Handles contracts, legal processes, and compliance.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config.settings import settings

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
            "lawsuit_management",
            "compliance_tracking",
            "deadline_monitoring"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Import routers
from services.legal.routers import contracts, lawsuits, deadlines

# Include routers
app.include_router(contracts.router, prefix="/contracts", tags=["Contracts"])
app.include_router(lawsuits.router, prefix="/lawsuits", tags=["Lawsuit Management"])
app.include_router(deadlines.router, prefix="/deadlines", tags=["Deadline Monitoring"])


if __name__ == "__main__":
    port = int(settings.legal_service_port)
    uvicorn.run("services.legal.main:app", host="0.0.0.0", port=port, reload=True)