"""
Global configuration settings for the Cortex backend.
"""

from typing import Any, Dict, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, computed_field


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: str = Field(default="development")
    debug: bool = Field(default=True)

    # Database
    database_host: str = Field(default="localhost")
    database_port: int = Field(default=5432)
    database_name: str = Field(default="cortex_db")
    database_user: str = Field(default="cortex_user")
    database_password: str = Field(default="")

    @computed_field
    @property
    def database_url(self) -> str:
        """Construct database URL from components."""
        return (
            f"postgresql+asyncpg://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )

    @computed_field
    @property
    def sync_database_url(self) -> str:
        """Construct synchronous database URL for Alembic."""
        return (
            f"postgresql://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )

    # Redis
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)

    @computed_field
    @property
    def redis_url(self) -> str:
        """Construct Redis URL."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    @computed_field
    @property
    def celery_broker_url(self) -> str:
        """Construct Celery broker URL (uses Redis)."""
        return f"redis://{self.redis_host}:{self.redis_port}/0"
    
    @computed_field
    @property
    def celery_backend_url(self) -> str:
        """Construct Celery backend URL (uses Redis)."""
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    # Security
    secret_key: str = Field(default="change-this-in-production")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)

    # OpenAI
    openai_api_key: Optional[str] = Field(default=None)

    # AWS
    aws_access_key_id: Optional[str] = Field(default=None)
    aws_secret_access_key: Optional[str] = Field(default=None)
    aws_region: str = Field(default="us-east-1")
    s3_bucket_name: Optional[str] = Field(default=None)

    # Service Ports
    gateway_port: int = Field(default=8000)
    auth_service_port: int = Field(default=8001)
    financial_service_port: int = Field(default=8002)
    hr_service_port: int = Field(default=8003)
    legal_service_port: int = Field(default=8004)
    procurement_service_port: int = Field(default=8005)
    documents_service_port: int = Field(default=8006)
    ai_service_port: int = Field(default=8007)

    # Service URLs
    auth_service_url: str = Field(default="http://localhost:8001")
    financial_service_url: str = Field(default="http://localhost:8002")
    hr_service_url: str = Field(default="http://localhost:8003")
    legal_service_url: str = Field(default="http://localhost:8004")
    procurement_service_url: str = Field(default="http://localhost:8005")
    documents_service_url: str = Field(default="http://localhost:8006")
    ai_service_url: str = Field(default="http://localhost:8007")

    # Sentry
    sentry_dsn: Optional[str] = Field(default=None)


# Create a singleton instance
settings = Settings()