"""
FastAPI dependency injection functions for authentication.

This module provides FastAPI dependencies that can be used in route handlers
to require authentication and extract user information.
"""

from typing import Optional

from fastapi import Cookie, Depends, HTTPException, Request, status

from .config import settings
from .exceptions import TokenMissingError
from .models import User
from .utils import create_user_from_token, extract_token_from_cookie


async def get_current_user(request: Request) -> User:
    """
    FastAPI dependency to get current authenticated user from request state.

    This dependency should be used after a decorator that validates the token
    and sets request.state.user.

    Args:
        request: FastAPI request object

    Returns:
        Current authenticated User

    Raises:
        HTTPException: 401 if user not found in request state

    Example:
        ```python
        @app.get("/protected")
        @require_auth
        async def protected_route(user: User = Depends(get_current_user)):
            return {"message": f"Hello {user.name}"}
        ```
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "token_missing", "message": "Authentication required"},
        )
    return request.state.user


async def get_current_user_from_cookie(
    request: Request,
    cortex_access_token: Optional[str] = Cookie(None, alias=settings.auth_cookie_name),
) -> User:
    """
    FastAPI dependency to validate JWT from cookie and extract user.

    This is an alternative to using decorators - it handles both token extraction
    and validation in one dependency.

    Args:
        request: FastAPI request object
        cortex_access_token: JWT token from httpOnly cookie

    Returns:
        Current authenticated User

    Raises:
        HTTPException: 401 if token missing, expired, or invalid

    Example:
        ```python
        @app.get("/protected")
        async def protected_route(user: User = Depends(get_current_user_from_cookie)):
            return {"message": f"Hello {user.name}"}
        ```
    """
    if not cortex_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "token_missing", "message": "Authentication required"},
        )

    try:
        user = create_user_from_token(cortex_access_token)
        # Store in request state for potential reuse
        request.state.user = user
        return user
    except Exception as e:
        # All auth exceptions inherit from our custom exceptions
        # which have status_code and code attributes
        if hasattr(e, "status_code") and hasattr(e, "code"):
            raise HTTPException(
                status_code=e.status_code,
                detail={"code": e.code, "message": str(e)},
            )
        # Fallback for unexpected exceptions
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "token_invalid", "message": "Invalid access token"},
        )


async def get_optional_user(
    request: Request,
    cortex_access_token: Optional[str] = Cookie(None, alias=settings.auth_cookie_name),
) -> Optional[User]:
    """
    FastAPI dependency to get user if authenticated, None otherwise.

    Useful for endpoints that have different behavior for authenticated users
    but don't require authentication.

    Args:
        request: FastAPI request object
        cortex_access_token: JWT token from httpOnly cookie

    Returns:
        User if authenticated, None otherwise (never raises authentication errors)

    Example:
        ```python
        @app.get("/public")
        async def public_route(user: Optional[User] = Depends(get_optional_user)):
            if user:
                return {"message": f"Hello {user.name}"}
            return {"message": "Hello guest"}
        ```
    """
    if not cortex_access_token:
        return None

    try:
        user = create_user_from_token(cortex_access_token)
        request.state.user = user
        return user
    except Exception:
        # Silently fail for optional authentication
        return None


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    FastAPI dependency to require admin role.

    Args:
        current_user: Current authenticated user

    Returns:
        User if they have admin role

    Raises:
        HTTPException: 403 if user lacks admin role

    Example:
        ```python
        @app.delete("/users/{user_id}")
        @require_auth
        async def delete_user(
            user_id: int,
            admin: User = Depends(require_admin)
        ):
            # Only admins can delete users
            return {"message": "User deleted"}
        ```
    """
    if not current_user.has_role("admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "insufficient_permissions",
                "message": "Admin role required",
            },
        )
    return current_user


def require_manager(current_user: User = Depends(get_current_user)) -> User:
    """
    FastAPI dependency to require manager or admin role.

    Args:
        current_user: Current authenticated user

    Returns:
        User if they have manager or admin role

    Raises:
        HTTPException: 403 if user lacks manager/admin role

    Example:
        ```python
        @app.post("/reports")
        @require_auth
        async def create_report(
            manager: User = Depends(require_manager)
        ):
            # Only managers and admins can create reports
            return {"message": "Report created"}
        ```
    """
    if not current_user.has_any_role(["manager", "admin"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "insufficient_permissions",
                "message": "Manager or admin role required",
            },
        )
    return current_user
