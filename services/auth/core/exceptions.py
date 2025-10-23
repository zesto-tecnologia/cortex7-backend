"""Custom exceptions for the authentication service."""

from typing import Optional, Any
from fastapi import HTTPException, status


class AuthServiceException(Exception):
    """Base exception for authentication service."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AuthenticationError(AuthServiceException):
    """Raised when authentication fails."""

    pass


class AuthorizationError(AuthServiceException):
    """Raised when authorization fails."""

    pass


class TokenError(AuthServiceException):
    """Raised for token-related errors."""

    pass


# Specific JWT Token Exceptions (Expert recommendation: Clear error differentiation)
class InvalidTokenError(TokenError):
    """Raised when token is invalid or malformed."""

    pass


class TokenExpiredError(TokenError):
    """Raised when token has expired."""

    pass


class TokenRevokedError(TokenError):
    """Raised when token has been revoked."""

    pass


class TokenReuseError(TokenError):
    """Raised when refresh token reuse is detected (security breach)."""

    pass


class ValidationError(AuthServiceException):
    """Raised for validation errors."""

    pass


class UserExistsError(AuthServiceException):
    """Raised when attempting to register a user that already exists."""

    pass



class UserNotFoundError(AuthServiceException):
    """Raised when user is not found."""

    pass


# HTTP Exceptions
class BadRequestError(HTTPException):
    """400 Bad Request error."""

    def __init__(self, detail: str, headers: Optional[dict[str, str]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            headers=headers
        )


class UnauthorizedError(HTTPException):
    """401 Unauthorized error."""

    def __init__(self, detail: str = "Could not validate credentials", headers: Optional[dict[str, str]] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers=headers or {"WWW-Authenticate": "Bearer"}
        )


class ForbiddenError(HTTPException):
    """403 Forbidden error."""

    def __init__(self, detail: str = "Not enough permissions", headers: Optional[dict[str, str]] = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            headers=headers
        )


class NotFoundError(HTTPException):
    """404 Not Found error."""

    def __init__(self, detail: str = "Resource not found", headers: Optional[dict[str, str]] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            headers=headers
        )


class ConflictError(HTTPException):
    """409 Conflict error."""

    def __init__(self, detail: str = "Resource conflict", headers: Optional[dict[str, str]] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            headers=headers
        )


class RateLimitError(HTTPException):
    """429 Too Many Requests error."""

    def __init__(self, detail: str = "Rate limit exceeded", headers: Optional[dict[str, str]] = None):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers=headers
        )


class InternalServerError(HTTPException):
    """500 Internal Server Error."""

    def __init__(self, detail: str = "Internal server error", headers: Optional[dict[str, str]] = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            headers=headers
        )