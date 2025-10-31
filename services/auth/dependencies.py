"""Common dependencies for FastAPI routes."""

from typing import Annotated
from uuid import UUID
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from services.auth.database import get_db
from services.auth.config import settings
from services.auth.core.exceptions import UnauthorizedError
from services.auth.services.jwt_service import JWTService


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
    authorization: Annotated[str | None, Header()] = None,
    db: DatabaseDependency = None
) -> UUID:
    """
    Extract user ID from authorization header by decoding JWT token.

    Args:
        authorization: Bearer token from Authorization header
        db: Database session for JWT service

    Returns:
        User UUID from token

    Raises:
        UnauthorizedError: If authorization header is missing or token is invalid
    """
    if not authorization:
        raise UnauthorizedError("Missing authorization header")

    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError("Invalid authorization header format. Expected: Bearer <token>")

    token = parts[1]

    try:
        # Decode and verify JWT token
        jwt_service = JWTService(db)
        payload = await jwt_service.verify_token(token, token_type="access")

        # Extract user ID from 'sub' claim
        user_id = UUID(payload["sub"])
        return user_id

    except Exception as e:
        raise UnauthorizedError(f"Invalid or expired token: {str(e)}")


CurrentUserDependency = Annotated[UUID, Depends(get_current_user_id)]


async def get_current_user(
    user_id: CurrentUserDependency,
    db: DatabaseDependency
):
    """
    Get current user object from database.

    Args:
        user_id: User ID from JWT token
        db: Database session

    Returns:
        User object

    Raises:
        UnauthorizedError: If user not found
    """
    from services.auth.repositories.user_repository import UserRepository

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise UnauthorizedError("User not found")

    return user


async def require_admin(current_user=Depends(get_current_user)):
    """
    Dependency to require admin role.

    Args:
        current_user: Current user object

    Returns:
        User object if admin

    Raises:
        ForbiddenError: If user is not admin or super_admin
    """
    from services.auth.core.exceptions import ForbiddenError

    if current_user.role not in ["admin", "super_admin"]:
        raise ForbiddenError("Admin access required")

    return current_user


async def require_admin_or_manager(current_user=Depends(get_current_user)):
    """
    Dependency to require admin or manager role.

    Args:
        current_user: Current user object

    Returns:
        User object if admin/manager

    Raises:
        ForbiddenError: If user is not admin, super_admin, or manager
    """
    from services.auth.core.exceptions import ForbiddenError

    if current_user.role not in ["admin", "super_admin", "manager"]:
        raise ForbiddenError("Admin or manager access required")

    return current_user


AdminDependency = Annotated[object, Depends(require_admin)]
AdminOrManagerDependency = Annotated[object, Depends(require_admin_or_manager)]


async def get_audit_service(db: DatabaseDependency):
    """Get audit service instance.

    Args:
        db: Database session

    Returns:
        AuditService instance
    """
    from services.auth.services.audit_service import AuditService
    return AuditService(db)


AuditServiceDependency = Annotated[object, Depends(get_audit_service)]