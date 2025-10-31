"""
Authentication middleware for the Gateway service.
"""

import logging
import random
from typing import Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from cortex_auth import (
    extract_token_from_cookie,
    decode_token,
    create_user_from_token,
    TokenMissingError,
    TokenExpiredError,
    TokenInvalidError,
    AuthenticationError,
)
from cortex_auth import settings as auth_settings
from .config import settings as gateway_settings
from .metrics import auth_metrics

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for JWT authentication with canary deployment support.

    Features:
    - Validates JWT tokens from httpOnly cookies
    - Supports public endpoint exclusions
    - Implements canary deployment (gradual rollout)
    - Tracks authentication metrics
    - Forwards authenticated user to request state
    """

    def __init__(self, app):
        super().__init__(app)
        self.public_endpoints = set(gateway_settings.public_endpoints)
        self.public_prefixes = gateway_settings.public_path_prefixes

        logger.info(
            f"Authentication middleware initialized "
            f"(canary: {gateway_settings.canary_enabled}, "
            f"percentage: {gateway_settings.canary_auth_percentage}%)"
        )

    def is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public (no auth required)."""
        # Exact match
        if path in self.public_endpoints:
            return True

        # Prefix match
        for prefix in self.public_prefixes:
            if path.startswith(prefix):
                return True

        return False

    def should_authenticate(self, request: Request) -> bool:
        """
        Determine if request should be authenticated based on canary settings.

        Canary deployment logic:
        - If canary disabled: authenticate all non-public requests
        - If canary enabled: randomly authenticate X% of traffic
        """
        # Always skip public endpoints
        if self.is_public_endpoint(request.url.path):
            return False

        # If auth disabled globally, skip all
        if not gateway_settings.auth_enabled:
            return False

        # If canary disabled, authenticate all
        if not gateway_settings.canary_enabled:
            return True

        # Canary: randomly select percentage of traffic
        random_value = random.randint(1, 100)
        should_auth = random_value <= gateway_settings.canary_auth_percentage

        if gateway_settings.metrics_enabled:
            auth_metrics.canary_requests_total.labels(
                authenticated=str(should_auth).lower()
            ).inc()

        return should_auth

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with optional authentication."""

        # Determine if this request needs authentication
        requires_auth = self.should_authenticate(request)

        if not requires_auth:
            # Public endpoint or not in canary sample - skip auth
            logger.debug(f"Skipping auth for: {request.url.path}")
            return await call_next(request)

        # Authenticate request
        try:
            # Extract token from httpOnly cookie
            token = extract_token_from_cookie(request)

            if not token:
                raise TokenMissingError("Authentication required")

            # Decode and validate JWT
            payload = decode_token(token, auth_settings.auth_public_key)

            # Create user object and attach to request state
            user = create_user_from_token(payload)
            request.state.user = user
            request.state.authenticated = True

            # Track successful authentication
            if gateway_settings.metrics_enabled:
                auth_metrics.auth_validations_total.labels(
                    result="success",
                    service="gateway"
                ).inc()

            logger.debug(
                f"Authenticated user {user.email} for {request.url.path}"
            )

            # Process request
            response = await call_next(request)
            return response

        except TokenMissingError as e:
            logger.warning(f"Missing token: {request.url.path}")

            if gateway_settings.metrics_enabled:
                auth_metrics.auth_validations_total.labels(
                    result="token_missing",
                    service="gateway"
                ).inc()

            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": {
                        "code": "token_missing",
                        "message": "Authentication required. Please log in.",
                        "detail": str(e)
                    }
                }
            )

        except TokenExpiredError as e:
            logger.warning(f"Expired token: {request.url.path}")

            if gateway_settings.metrics_enabled:
                auth_metrics.auth_validations_total.labels(
                    result="token_expired",
                    service="gateway"
                ).inc()

            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": {
                        "code": "token_expired",
                        "message": "Access token has expired. Please refresh.",
                        "detail": str(e)
                    }
                }
            )

        except TokenInvalidError as e:
            logger.error(f"Invalid token: {request.url.path} - {e}")

            if gateway_settings.metrics_enabled:
                auth_metrics.auth_validations_total.labels(
                    result="token_invalid",
                    service="gateway"
                ).inc()

            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": {
                        "code": "token_invalid",
                        "message": "Invalid authentication token.",
                        "detail": str(e)
                    }
                }
            )

        except AuthenticationError as e:
            logger.error(f"Authentication error: {request.url.path} - {e}")

            if gateway_settings.metrics_enabled:
                auth_metrics.auth_validations_total.labels(
                    result="auth_error",
                    service="gateway"
                ).inc()

            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": {
                        "code": "authentication_failed",
                        "message": "Authentication failed.",
                        "detail": str(e)
                    }
                }
            )

        except Exception as e:
            logger.exception(f"Unexpected auth error: {request.url.path}")

            if gateway_settings.metrics_enabled:
                auth_metrics.auth_validations_total.labels(
                    result="unexpected_error",
                    service="gateway"
                ).inc()

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": {
                        "code": "internal_error",
                        "message": "Internal server error during authentication.",
                    }
                }
            )
