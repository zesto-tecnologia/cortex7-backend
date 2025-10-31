"""
HR microservice main application.
Handles employee management, contracts, and HR operations.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config.settings import settings

# Create FastAPI app
app = FastAPI(
    title="HR Service",
    description="Human Resources management microservice",
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
        "service": "HR Service",
        "version": "1.0.0",
        "status": "operational",
        "features": [
            "employee_management",
            "contracts",
            "vacation_tracking",
            "benefits_management"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Import routers
from services.hr.routers import employees, contracts, vacations, benefits

# Include routers
app.include_router(employees.router, prefix="/employees", tags=["Employees"])
app.include_router(contracts.router, prefix="/contracts", tags=["Employment Contracts"])
app.include_router(vacations.router, prefix="/vacations", tags=["Vacations"])
app.include_router(benefits.router, prefix="/benefits", tags=["Benefits"])


if __name__ == "__main__":
    port = int(settings.hr_service_port)
    uvicorn.run("services.hr.main:app", host="0.0.0.0", port=port, reload=True)