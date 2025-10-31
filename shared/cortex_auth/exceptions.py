"""
Custom exceptions for cortex-auth library.

This module defines authentication and authorization exceptions used throughout
the cortex-auth library and by services that integrate with it.
"""

from fastapi import status


class AuthenticationError(Exception):
    """Base exception for authentication errors."""

    def __init__(self, message: str = "Authentication failed", code: str = "auth_failed"):
        self.message = message
        self.code = code
        self.status_code = status.HTTP_401_UNAUTHORIZED
        super().__init__(self.message)


class TokenMissingError(AuthenticationError):
    """Raised when no authentication token is provided."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message=message, code="token_missing")


class TokenExpiredError(AuthenticationError):
    """Raised when the JWT token has expired."""

    def __init__(self, message: str = "Access token has expired"):
        super().__init__(message=message, code="token_expired")


class TokenInvalidError(AuthenticationError):
    """Raised when the JWT token is invalid or malformed."""

    def __init__(self, message: str = "Invalid access token"):
        super().__init__(message=message, code="token_invalid")


class IssuerInvalidError(AuthenticationError):
    """Raised when the JWT token issuer is invalid."""

    def __init__(self, message: str = "Invalid token issuer"):
        super().__init__(message=message, code="issuer_invalid")


class AuthorizationError(Exception):
    """Base exception for authorization errors."""

    def __init__(self, message: str = "Access denied", code: str = "access_denied"):
        self.message = message
        self.code = code
        self.status_code = status.HTTP_403_FORBIDDEN
        super().__init__(self.message)


class InsufficientPermissionsError(AuthorizationError):
    """Raised when user lacks required permissions."""

    def __init__(self, message: str = "Insufficient permissions", required_roles: list[str] | None = None):
        if required_roles:
            message = f"{message}. Required roles: {', '.join(required_roles)}"
        super().__init__(message=message, code="insufficient_permissions")
        self.required_roles = required_roles or []


class RoleRequiredError(AuthorizationError):
    """Raised when user lacks required role."""

    def __init__(self, required_roles: list[str]):
        message = f"Required roles: {', '.join(required_roles)}"
        super().__init__(message=message, code="role_required")
        self.required_roles = required_roles
