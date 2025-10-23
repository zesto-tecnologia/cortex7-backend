"""Common dependencies for FastAPI routes."""

from typing import Annotated
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from services.auth.database import get_db
from services.auth.config import settings
from services.auth.core.exceptions import UnauthorizedError


async def get_redis() -> Redis:
    """Get Redis connection."""
    redis = Redis.from_url(str(settings.REDIS_URL))
    try:
        yield redis
    finally:
        await redis.close()


# Type aliases for dependency injection
DatabaseDependency = Annotated[AsyncSession, Depends(get_db)]
RedisDependency = Annotated[Redis, Depends(get_redis)]


async def get_current_user_id(
    authorization: Annotated[str | None, Header()] = None
) -> str:
    """
    Extract user ID from authorization header.

    This is a placeholder - actual implementation will decode JWT.
    """
    if not authorization:
        raise UnauthorizedError("Missing authorization header")

    # TODO: Implement JWT decoding
    # For now, return a placeholder
    return "placeholder-user-id"


CurrentUserDependency = Annotated[str, Depends(get_current_user_id)]