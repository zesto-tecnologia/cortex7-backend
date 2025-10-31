"""
Utility functions for JWT validation and permission checking.

This module provides core authentication and authorization utilities used
by decorators and dependencies.
"""

from datetime import datetime, timezone
from typing import Any

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from .config import settings
from .exceptions import IssuerInvalidError, TokenExpiredError, TokenInvalidError
from .models import User


def decode_token(token: str, public_key: str | None = None) -> dict[str, Any]:
    """
    Decode and validate JWT with RS256 public key.

    Args:
        token: JWT token string
        public_key: Optional RSA public key (uses settings if not provided)

    Returns:
        Decoded token payload as dictionary

    Raises:
        TokenInvalidError: If token is malformed or signature is invalid
        TokenExpiredError: If token has expired
        IssuerInvalidError: If token issuer is invalid
    """
    if public_key is None:
        public_key = settings.get_public_key()

    try:
        # Decode JWT with RS256 algorithm
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_aud": False},  # No audience claim in our tokens
        )

        # Verify issuer
        if payload.get("iss") != settings.auth_issuer:
            raise IssuerInvalidError(
                f"Expected issuer '{settings.auth_issuer}', got '{payload.get('iss')}'"
            )

        # Verify expiration with clock skew tolerance
        if "exp" in payload:
            now = datetime.now(timezone.utc).timestamp()
            # Allow clock skew tolerance (default ±60 seconds)
            if payload["exp"] < now - settings.auth_clock_skew_seconds:
                raise TokenExpiredError("Token has expired")

        return payload

    except TokenExpiredError:
        raise
    except IssuerInvalidError:
        raise
    except ExpiredSignatureError:
        # Jose's built-in expiration check detected expired token
        raise TokenExpiredError("Token has expired")
    except JWTError as e:
        raise TokenInvalidError(f"Token validation failed: {str(e)}")
    except Exception as e:
        raise TokenInvalidError(f"Unexpected error during token validation: {str(e)}")


def create_user_from_token(token: str, public_key: str | None = None) -> User:
    """
    Decode token and create User instance.

    Args:
        token: JWT token string
        public_key: Optional RSA public key (uses settings if not provided)

    Returns:
        User instance with data from token

    Raises:
        TokenInvalidError: If token is invalid
        TokenExpiredError: If token has expired
        IssuerInvalidError: If token issuer is invalid
    """
    payload = decode_token(token, public_key)
    return User.from_token_payload(payload)


def verify_roles(user: User, required_roles: list[str]) -> bool:
    """
    Check if user has at least one of the required roles.

    Args:
        user: User instance to check
        required_roles: List of acceptable roles (OR logic)

    Returns:
        True if user has any of the required roles, False otherwise
    """
    if not required_roles:
        return True  # No roles required
    return user.has_any_role(required_roles)


def verify_all_roles(user: User, required_roles: list[str]) -> bool:
    """
    Check if user has all required roles.

    Args:
        user: User instance to check
        required_roles: List of required roles (AND logic)

    Returns:
        True if user has all required roles, False otherwise
    """
    if not required_roles:
        return True  # No roles required
    return user.has_all_roles(required_roles)


def verify_permissions(user: User, required_permissions: list[str]) -> bool:
    """
    Check if user has all required permissions.

    Supports wildcard permissions:
    - "*:*" grants all permissions
    - "*:resource" grants all actions on resource
    - "action:*" grants action on all resources

    Args:
        user: User instance to check
        required_permissions: List of required permission strings (format: "action:resource")

    Returns:
        True if user has all required permissions, False otherwise
    """
    if not required_permissions:
        return True  # No permissions required

    return user.has_all_permissions(required_permissions)


def verify_any_permission(user: User, required_permissions: list[str]) -> bool:
    """
    Check if user has at least one of the required permissions.

    Args:
        user: User instance to check
        required_permissions: List of acceptable permissions (OR logic)

    Returns:
        True if user has any of the required permissions, False otherwise
    """
    if not required_permissions:
        return True  # No permissions required

    return any(user.has_permission(perm) for perm in required_permissions)


def extract_token_from_cookie(cookies: dict[str, str]) -> str | None:
    """
    Extract JWT token from httpOnly cookie.

    Args:
        cookies: Dictionary of cookies from request

    Returns:
        Token string if found, None otherwise
    """
    return cookies.get(settings.auth_cookie_name)


def is_admin(user: User) -> bool:
    """
    Check if user has admin role.

    Args:
        user: User instance to check

    Returns:
        True if user has admin role, False otherwise
    """
    return user.has_role("admin")


def is_manager(user: User) -> bool:
    """
    Check if user has manager role.

    Args:
        user: User instance to check

    Returns:
        True if user has manager role, False otherwise
    """
    return user.has_role("manager")
