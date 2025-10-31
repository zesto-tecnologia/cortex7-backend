"""
Gateway service configuration.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class GatewaySettings(BaseSettings):
    """Gateway-specific settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="GATEWAY_",
        extra="ignore",
    )

    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins for the gateway"
    )
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: List[str] = Field(default=["*"])
    cors_allow_headers: List[str] = Field(default=["*"])

    # Authentication
    auth_enabled: bool = Field(
        default=True,
        description="Enable authentication middleware"
    )

    # Canary Deployment
    canary_auth_percentage: int = Field(
        default=10,
        description="Percentage of traffic to route through authenticated path (0-100)"
    )
    canary_enabled: bool = Field(
        default=True,
        description="Enable canary deployment for gradual rollout"
    )

    # Public Endpoints (no auth required)
    public_endpoints: List[str] = Field(
        default=[
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/metrics",
            "/auth/login",
            "/auth/register",
            "/auth/refresh",
        ],
        description="Endpoints that don't require authentication"
    )

    # Service-specific public routes (path prefixes that don't need auth)
    public_path_prefixes: List[str] = Field(
        default=[
            "/auth/api/v1/auth/login",
            "/auth/api/v1/auth/register",
            "/auth/api/v1/auth/refresh",
            "/api/v1/ppt",
            "/api/export-as-pdf",
            "/api/v1/webhook",
            "/api/v1/mock",
            "/static",
            "/app_data",
        ],
        description="Path prefixes that bypass authentication"
    )

    # Monitoring
    metrics_enabled: bool = Field(default=True)
    log_auth_failures: bool = Field(default=True)


settings = GatewaySettings()
