"""Token Introspection Service for JWT validation and metadata retrieval.

This service implements OAuth 2.0 Token Introspection (RFC 7662) for:
- Token validation without decryption (Kong Gateway use)
- Token metadata retrieval
- Active/inactive token status
- Token revocation support
"""

from typing import Any, Optional
from datetime import datetime, timezone
import jwt
import structlog

from services.auth.services.jwt_service import JWTService
from services.auth.core.exceptions import InvalidTokenError, TokenExpiredError, TokenRevokedError
from services.auth.core.cache import redis_client

logger = structlog.get_logger(__name__)


class TokenIntrospectionService:
    """Token introspection for validation and metadata retrieval."""

    def __init__(self, jwt_service: JWTService):
        """Initialize introspection service.

        Args:
            jwt_service: JWT service instance for token verification
        """
        self.jwt_service = jwt_service

    async def introspect(
        self,
        token: str,
        token_type_hint: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Introspect token and return metadata (RFC 7662 compliant).

        This endpoint is primarily for Kong Gateway to validate tokens
        and retrieve claims without decryption.

        Args:
            token: JWT token string
            token_type_hint: Optional hint about token type ("access" or "refresh")

        Returns:
            Introspection response with:
            - active: bool (True if token is valid)
            - scope: string (space-separated permissions)
            - client_id: string
            - username: string (email)
            - token_type: string
            - exp, iat, nbf, sub, jti: token claims
            - Custom claims (role, company_id, etc.)
        """
        try:
            # Try to decode without verification first to get type
            unverified = jwt.decode(
                token,
                options={"verify_signature": False, "verify_exp": False}
            )

            token_type = token_type_hint or unverified.get("token_type", "access")

            # Verify token with full validation
            payload = await self.jwt_service.verify_token(token, token_type)

            # Build RFC 7662 compliant introspection response
            response = {
                "active": True,
                "scope": " ".join(payload.get("permissions", [])),
                "client_id": payload.get("iss", "auth-service"),
                "username": payload.get("email"),
                "token_type": token_type,
                "exp": payload.get("exp"),
                "iat": payload.get("iat"),
                "nbf": payload.get("nbf"),
                "sub": payload.get("sub"),
                "aud": payload.get("aud"),
                "iss": payload.get("iss"),
                "jti": payload.get("jti"),
            }

            # Add custom claims
            if "role" in payload:
                response["role"] = payload["role"]
            if "company_id" in payload:
                response["company_id"] = payload["company_id"]
            if "email" in payload:
                response["email"] = payload["email"]
            if "name" in payload:
                response["name"] = payload["name"]

            logger.info(
                "Token introspection successful",
                token_type=token_type,
                jti=payload.get("jti"),
                active=True
            )

            return response

        except (TokenExpiredError, TokenRevokedError, InvalidTokenError) as e:
            logger.info("Token introspection failed", error=str(e), active=False)
            return {"active": False}
        except Exception as e:
            logger.error("Introspection error", error=str(e))
            return {"active": False}

    async def revoke_token(self, token: str) -> bool:
        """
        Revoke a token by marking it invalid.

        Supports revoking both active and expired tokens for security.

        Args:
            token: JWT token string to revoke

        Returns:
            True if token was revoked, False if revocation failed
        """
        try:
            # Decode without expiration check (allow revoking expired tokens)
            payload = jwt.decode(
                token,
                self.jwt_service.public_key,
                algorithms=[self.jwt_service.algorithm],
                options={"verify_exp": False}  # Allow revoking expired tokens
            )

            token_id = payload.get("jti")
            if not token_id:
                logger.warning("Token missing JTI, cannot revoke")
                return False

            # Revoke through JWT service
            await self.jwt_service.revoke_token(token_id)

            logger.info("Token revoked via introspection", jti=token_id)
            return True

        except Exception as e:
            logger.error("Token revocation failed", error=str(e))
            return False

    async def get_token_info(self, token: str) -> dict[str, Any]:
        """
        Get detailed token information for debugging/auditing.

        Args:
            token: JWT token string

        Returns:
            Detailed token information including all claims
        """
        try:
            # Get full payload
            payload = jwt.decode(
                token,
                self.jwt_service.public_key,
                algorithms=[self.jwt_service.algorithm],
                options={"verify_exp": False}
            )

            # Calculate expiration status
            exp_timestamp = payload.get("exp", 0)
            exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            is_expired = exp_datetime < datetime.now(timezone.utc)

            # Check revocation status
            jti = payload.get("jti")
            is_revoked = await self.jwt_service._is_token_revoked(jti) if jti else False

            return {
                "payload": payload,
                "is_expired": is_expired,
                "is_revoked": is_revoked,
                "expires_at": exp_datetime.isoformat(),
                "issued_at": datetime.fromtimestamp(
                    payload.get("iat", 0), tz=timezone.utc
                ).isoformat(),
                "valid": not is_expired and not is_revoked
            }

        except Exception as e:
            logger.error("Failed to get token info", error=str(e))
            return {"error": str(e), "valid": False}
