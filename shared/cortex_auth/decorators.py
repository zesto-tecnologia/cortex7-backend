"""
FastAPI route decorators for authentication and authorization.

This module provides decorators that can be applied to FastAPI route handlers
to enforce authentication and role-based access control.
"""

from functools import wraps
from typing import Callable, List, Optional

from fastapi import HTTPException, Request, status

from .config import settings
from .exceptions import (
    InsufficientPermissionsError,
    IssuerInvalidError,
    TokenExpiredError,
    TokenInvalidError,
    TokenMissingError,
)
from .utils import (
    create_user_from_token,
    extract_token_from_cookie,
    verify_permissions,
    verify_roles,
)


def require_auth(func: Callable) -> Callable:
    """
    Decorator to require authentication for a FastAPI endpoint.

    Extracts JWT from httpOnly cookie, validates it, and attaches User
    to request.state.user for downstream dependencies.

    Args:
        func: FastAPI route handler function

    Returns:
        Wrapped function that validates authentication

    Raises:
        HTTPException: 401 if authentication fails

    Example:
        ```python
        @app.get("/protected")
        @require_auth
        async def protected_route(request: Request):
            user = request.state.user
            return {"message": f"Hello {user.name}"}
        ```
    """

    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        # Check if auth is enabled (useful for testing)
        if not settings.auth_enabled:
            # Create a mock user for testing
            from .models import User

            request.state.user = User(
                user_id="test-user-id",
                email="test@example.com",
                name="Test User",
                roles=["user"],
                permissions=["*:*"],
            )
            return await func(request, *args, **kwargs)

        # Extract token from httpOnly cookie
        token = extract_token_from_cookie(request.cookies)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "token_missing", "message": "Authentication required"},
            )

        try:
            # Validate JWT and create User instance
            user = create_user_from_token(token)
            request.state.user = user
            return await func(request, *args, **kwargs)

        except TokenExpiredError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": e.code, "message": e.message},
            )
        except TokenInvalidError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": e.code, "message": e.message},
            )
        except TokenMissingError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": e.code, "message": e.message},
            )
        except InsufficientPermissionsError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": e.code, "message": e.message},
            )
        except HTTPException:
            # Re-raise HTTP exceptions from downstream decorators unchanged
            raise
        except (IssuerInvalidError, Exception) as e:
            # Handle IssuerInvalidError and other unexpected errors
            if isinstance(e, IssuerInvalidError):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={"code": e.code, "message": e.message},
                )
            # Catch-all for unexpected errors
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "auth_failed", "message": f"Authentication failed: {str(e)}"},
            )

    return wrapper


def require_roles(roles: List[str], require_all: bool = False) -> Callable:
    """
    Decorator to require specific roles for a FastAPI endpoint.

    Automatically applies @require_auth, then checks if user has required roles.

    Args:
        roles: List of required roles
        require_all: If True, user must have ALL roles (AND logic).
                    If False, user must have ANY role (OR logic). Default: False

    Returns:
        Decorator function

    Raises:
        HTTPException: 401 if not authenticated, 403 if lacking required roles

    Example:
        ```python
        # User must have admin OR manager role
        @app.delete("/users/{user_id}")
        @require_roles(["admin", "manager"])
        async def delete_user(request: Request, user_id: int):
            return {"message": "User deleted"}

        # User must have BOTH admin AND manager roles
        @app.post("/critical-action")
        @require_roles(["admin", "manager"], require_all=True)
        async def critical_action(request: Request):
            return {"message": "Action performed"}
        ```
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @require_auth  # Ensure authentication first
        async def wrapper(request: Request, *args, **kwargs):
            user = request.state.user

            # Check roles (OR logic by default, AND logic if require_all=True)
            if require_all:
                has_access = all(user.has_role(role) for role in roles)
            else:
                has_access = verify_roles(user, roles)

            if not has_access:
                logic = "all" if require_all else "any"
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "insufficient_permissions",
                        "message": f"Required roles ({logic} of): {', '.join(roles)}",
                    },
                )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_permissions(permissions: List[str], require_all: bool = True) -> Callable:
    """
    Decorator to require specific permissions for a FastAPI endpoint.

    Automatically applies @require_auth, then checks if user has required permissions.
    Supports wildcard permissions (*:* and *:resource).

    Args:
        permissions: List of required permission strings (format: "action:resource")
        require_all: If True, user must have ALL permissions (AND logic).
                    If False, user must have ANY permission (OR logic). Default: True

    Returns:
        Decorator function

    Raises:
        HTTPException: 401 if not authenticated, 403 if lacking required permissions

    Example:
        ```python
        # User must have both read and write permissions on documents
        @app.put("/documents/{doc_id}")
        @require_permissions(["read:documents", "write:documents"])
        async def update_document(request: Request, doc_id: int):
            return {"message": "Document updated"}

        # User must have ANY of the specified permissions
        @app.get("/reports")
        @require_permissions(["read:reports", "admin:reports"], require_all=False)
        async def get_reports(request: Request):
            return {"reports": []}
        ```
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @require_auth  # Ensure authentication first
        async def wrapper(request: Request, *args, **kwargs):
            user = request.state.user

            # Check permissions (AND logic by default, OR logic if require_all=False)
            if require_all:
                has_access = verify_permissions(user, permissions)
            else:
                has_access = any(user.has_permission(perm) for perm in permissions)

            if not has_access:
                logic = "all" if require_all else "any"
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "insufficient_permissions",
                        "message": f"Required permissions ({logic} of): {', '.join(permissions)}",
                    },
                )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_admin(func: Callable) -> Callable:
    """
    Decorator to require admin role for a FastAPI endpoint.

    Convenience decorator equivalent to @require_roles(["admin"]).

    Args:
        func: FastAPI route handler function

    Returns:
        Wrapped function that requires admin role

    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin

    Example:
        ```python
        @app.delete("/users/{user_id}")
        @require_admin
        async def delete_user(request: Request, user_id: int):
            return {"message": "User deleted"}
        ```
    """
    return require_roles(["admin"])(func)


def require_manager(func: Callable) -> Callable:
    """
    Decorator to require manager or admin role for a FastAPI endpoint.

    Convenience decorator equivalent to @require_roles(["manager", "admin"]).

    Args:
        func: FastAPI route handler function

    Returns:
        Wrapped function that requires manager or admin role

    Raises:
        HTTPException: 401 if not authenticated, 403 if not manager/admin

    Example:
        ```python
        @app.post("/reports")
        @require_manager
        async def create_report(request: Request):
            return {"message": "Report created"}
        ```
    """
    return require_roles(["manager", "admin"])(func)
