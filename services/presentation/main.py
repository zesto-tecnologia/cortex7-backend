"""Main FastAPI application for the presentation service."""

import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from services.presentation.api.main import app as presentation_app
from services.presentation.api.lifespan import app_lifespan


# Get settings
APP_NAME = "Cortex Presentation Service"
APP_VERSION = "0.1.0"
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8008"))
CORS_ORIGINS = ["*"]  # Configure as needed


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup - Use the original presentation app lifespan
    async with app_lifespan(app):
        yield


# Use the existing presentation app but update lifespan
app = presentation_app
app.title = APP_NAME
app.version = APP_VERSION
app.lifespan = lifespan


# Configure CORS (already configured in original app but ensure it's set)
if not any(isinstance(m, CORSMiddleware) for m in app.user_middleware):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Basic health check endpoint.

    Returns 200 if the service is running.
    """
    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION
    }


@app.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.

    Validates service is ready to accept requests.
    """
    # Add any specific readiness checks here
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "ready",
            "service": APP_NAME
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "services.presentation.main:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=True
    )
