"""Main FastAPI application for the authentication service."""

import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text
import httpx

from services.auth.config import settings
from services.auth.database import engine
from services.auth.schemas.auth import HealthResponse, ReadinessResponse
from services.auth.core.logging import configure_logging, get_logger
from services.auth.api.v1 import auth, users
from services.auth.core.cache import redis_client

# Configure logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"auth_service_starting - version={settings.APP_VERSION}, env={settings.ENVIRONMENT}")

    # Initialize Redis connection
    try:
        await redis_client.connect()
    except Exception as e:
        logger.error(f"redis_connection_failed - {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("auth_service_stopping")

    # Disconnect Redis
    try:
        await redis_client.disconnect()
    except Exception as e:
        logger.error(f"redis_disconnect_failed - {str(e)}")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.ENABLE_SWAGGER_UI else None,
    redoc_url="/redoc" if settings.ENABLE_SWAGGER_UI else None,
    lifespan=lifespan,
)

# Configure CORS
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check():
    """
    Basic health check endpoint.

    Returns 200 if the service is running.
    """
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION
    )


@app.get("/ready", response_model=ReadinessResponse)
async def readiness_check():
    """
    Readiness check endpoint.

    Validates all service dependencies:
    - PostgreSQL database
    - Redis cache
    - Supabase Auth service
    """
    dependencies = {}
    overall_status = "ready"

    # Check PostgreSQL
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        dependencies["postgresql"] = "healthy"
    except Exception as e:
        logger.error("postgresql_health_check_failed", error=str(e))
        dependencies["postgresql"] = f"unhealthy: {str(e)}"
        overall_status = "not_ready"

    # Check Redis
    try:
        await redis_client.ping()
        dependencies["redis"] = "healthy"
    except Exception as e:
        logger.error("redis_health_check_failed", error=str(e))
        dependencies["redis"] = f"unhealthy: {str(e)}"
        overall_status = "not_ready"

    # Check Supabase
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.SUPABASE_URL}/auth/v1/health",
                headers={
                    "apikey": settings.SUPABASE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_KEY}"
                },
                timeout=5
            )
            if response.status_code == 200:
                dependencies["supabase"] = "healthy"
            else:
                dependencies["supabase"] = f"unhealthy: status {response.status_code}"
                overall_status = "not_ready"
    except Exception as e:
        logger.error("supabase_health_check_failed", error=str(e))
        dependencies["supabase"] = f"unhealthy: {str(e)}"
        overall_status = "not_ready"

    status_code = (
        status.HTTP_200_OK if overall_status == "ready"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall_status,
            "dependencies": dependencies
        }
    )


# Include routers
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["authentication"]
)

app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["users"]
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", "8001"))
    uvicorn.run("services.auth.main:app", host="0.0.0.0", port=port, reload=True)