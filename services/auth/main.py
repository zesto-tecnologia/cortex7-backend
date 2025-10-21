"""
Auth microservice main application.
Handles authentication, authorization, and user management.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.config.settings import settings
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="Auth Service",
    description="Authentication and authorization microservice",
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
        "service": "Auth Service",
        "version": "1.0.0",
        "status": "operational",
        "features": [
            "authentication",
            "authorization",
            "user_management",
            "token_management"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    port = int(settings.auth_service_port)
    uvicorn.run(app, host="0.0.0.0", port=port)

