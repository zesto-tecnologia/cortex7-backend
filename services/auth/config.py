"""Application configuration using Pydantic V2 settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, RedisDsn, HttpUrl, Field, field_validator
from typing import Literal


class Settings(BaseSettings):
    """Application configuration using Pydantic V2 settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    APP_NAME: str = "auth-service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # Database - REQUIRED: Must be set in .env
    DATABASE_URL: PostgresDsn
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_ECHO: bool = False

    # Redis - REQUIRED: Must be set in .env
    REDIS_URL: RedisDsn
    REDIS_POOL_SIZE: int = 10
    REDIS_DECODE_RESPONSES: bool = True

    # Supabase - REQUIRED: Must be set in .env
    SUPABASE_URL: HttpUrl
    SUPABASE_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str

    # JWT
    JWT_ALGORITHM: str = "RS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 10
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ISSUER: str = "auth-service"
    JWT_AUDIENCE: str = "cortex-7"
    JWT_PRIVATE_KEY_PATH: str = "keys/jwt_private_key.pem"
    JWT_PUBLIC_KEY_PATH: str = "keys/jwt_public_key.pem"
    JWT_KEY_PASSWORD: str | None = None  # Optional password for encrypted keys
    JWT_KEY_ROTATION_DAYS: int = 90

    # Company Service - REQUIRED: Must be set in .env
    COMPANY_SERVICE_URL: HttpUrl
    COMPANY_SERVICE_TIMEOUT: int = 5

    # Frontend
    FRONTEND_URL: HttpUrl = Field(default="http://localhost:3000")

    # Security - REQUIRED: SECRET_KEY must be set in .env
    CORS_ORIGINS: list[str] = Field(default_factory=list)
    ALLOWED_HOSTS: list[str] = Field(default_factory=list)
    SECRET_KEY: str

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    LOGIN_RATE_LIMIT: int = 5  # requests per minute
    REGISTER_RATE_LIMIT: int = 3  # requests per hour
    REFRESH_RATE_LIMIT: int = 10  # requests per minute

    # Observability
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://otel-collector:4317"
    OTEL_SERVICE_NAME: str = "auth-service"
    PROMETHEUS_PORT: int = 9090
    SENTRY_DSN: str | None = None
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Feature Flags
    ENABLE_SWAGGER_UI: bool = True
    ENABLE_METRICS: bool = True
    ENABLE_TRACING: bool = True

    @field_validator("DATABASE_URL", mode="after")
    def assemble_db_connection(cls, v):
        """Convert PostgresDsn to string for SQLAlchemy."""
        if isinstance(v, str):
            return v
        return str(v)

    @field_validator("REDIS_URL", mode="after")
    def assemble_redis_connection(cls, v):
        """Convert RedisDsn to string for Redis client."""
        if isinstance(v, str):
            return v
        return str(v)


settings = Settings()