"""JWT Token Service with RS256 signing and token family management.

This service implements:
- RS256 asymmetric JWT signing for access and refresh tokens
- Token family tracking for refresh token rotation security
- Proper token revocation and reuse detection
- Redis caching for performance optimization

Expert recommendations implemented:
- Separate family ID (fid) claim for proper family chain propagation
- Family ID only created on initial login, propagated through rotations
- Public key used for token verification (separation of concerns)
- Custom exceptions for clear error handling
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Tuple
from uuid import UUID, uuid4
import hashlib
import json
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from services.auth.config import settings
from services.auth.core.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
    TokenRevokedError,
    TokenReuseError,
)
from services.auth.repositories.refresh_token_repository import RefreshTokenRepository
from services.auth.core.cache import redis_client

logger = structlog.get_logger(__name__)


class JWTService:
    """JWT token generation, validation, and rotation service with RS256 signing."""

    def __init__(self, session: AsyncSession):
        """Initialize JWT service with database session."""
        self.session = session
        self.token_repo = RefreshTokenRepository(session)
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        self.refresh_token_expire = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        self._load_keys()

    def _load_keys(self) -> None:
        """Load RSA keys for signing and verification."""
        try:
            # Load private key for signing
            with open(settings.JWT_PRIVATE_KEY_PATH, 'rb') as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=settings.JWT_KEY_PASSWORD.encode() if settings.JWT_KEY_PASSWORD else None,
                    backend=default_backend()
                )

            # Load public key for verification
            with open(settings.JWT_PUBLIC_KEY_PATH, 'rb') as f:
                self.public_key = serialization.load_pem_public_key(
                    f.read(),
                    backend=default_backend()
                )
        except Exception as e:
            logger.error(f"jwt_keys_load_failed - {str(e)}")
            raise

    async def _generate_token(
        self,
        user_id: UUID,
        token_type: str,
        expires_delta: timedelta,
        jti: str,
        family_id: Optional[str] = None,
        **extra_claims
    ) -> Tuple[str, str]:
        """
        Generate JWT token with proper claim structure.

        Args:
            user_id: User UUID
            token_type: "access" or "refresh"
            expires_delta: Token expiration time
            jti: Unique token ID
            family_id: Optional family ID for refresh tokens (fid claim)
            **extra_claims: Additional claims (email, role, permissions, etc.)

        Returns:
            Tuple of (encoded_token, jti)
        """
        now = datetime.now(timezone.utc)
        expire = now + expires_delta

        claims: dict[str, Any] = {
            "token_type": token_type,
            "exp": expire,
            "iat": now,
            "nbf": now,  # Not before (helps with clock skew)
            "jti": jti,
            "sub": str(user_id),
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
        }

        # Add family ID for refresh tokens (expert recommendation)
        if family_id and token_type == "refresh":
            claims["fid"] = family_id

        # Merge extra claims (email, role, permissions, etc.)
        claims.update(extra_claims)

        # Sign token with RS256
        encoded_token = jwt.encode(
            claims,
            self.private_key,
            algorithm=self.algorithm
        )

        return encoded_token, jti

    async def create_access_token(
        self,
        user_id: UUID,
        email: str,
        role: str,
        company_id: Optional[UUID] = None,
        permissions: Optional[list[str]] = None
    ) -> Tuple[str, str]:
        """
        Generate JWT access token with user claims.

        Implements role-based token lifetimes:
        - admin/super_admin/manager: 30 minutes (1800 seconds)
        - user: 60 minutes (3600 seconds)

        Args:
            user_id: User UUID
            email: User email
            role: User role (user, admin, super_admin, manager)
            company_id: Optional company UUID
            permissions: Optional list of permissions

        Returns:
            Tuple of (access_token, jti)
        """
        jti = str(uuid4())

        # Role-based token lifetime (Task 2.0 requirement)
        if role in ["admin", "super_admin", "manager"]:
            # Privileged roles: 30 minutes
            expires_delta = timedelta(seconds=settings.TOKEN_ACCESS_LIFETIME_ADMIN)
        else:
            # Regular users: 60 minutes
            expires_delta = timedelta(seconds=settings.TOKEN_ACCESS_LIFETIME_USER)

        extra_claims = {
            "email": email,
            "role": role,
            "permissions": permissions or [],
        }

        if company_id:
            extra_claims["company_id"] = str(company_id)

        # Cache token metadata for fast validation/revocation
        cache_key = f"token:{jti}"
        await redis_client.setex(
            cache_key,
            int(expires_delta.total_seconds()),
            json.dumps({
                "user_id": str(user_id),
                "valid": True,
                "type": "access"
            })
        )

        token, jti = await self._generate_token(
            user_id=user_id,
            token_type="access",
            expires_delta=expires_delta,
            jti=jti,
            **extra_claims
        )

        return token, jti

    async def create_refresh_token(
        self,
        user_id: UUID,
        token_family_id: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> str:
        """
        Generate refresh token with family tracking.

        EXPERT FIX: A new family is created only if no ID is provided (initial login).
        The first token's JTI serves as the family ID. During rotation, the existing
        family ID is propagated to maintain the family chain.

        Args:
            user_id: User UUID
            token_family_id: Optional existing family ID (for rotation)
            device_id: Optional device identifier

        Returns:
            Encoded refresh token
        """
        jti = str(uuid4())

        # CRITICAL: Create new family only on initial login
        # Expert recommendation - prevents breaking the family chain
        if token_family_id is None:
            token_family_id = jti  # First token's JTI becomes the family ID

        token, _ = await self._generate_token(
            user_id=user_id,
            token_type="refresh",
            expires_delta=self.refresh_token_expire,
            jti=jti,
            family_id=token_family_id,
            device_id=device_id
        )

        # Store hashed token in database
        token_hash = self._hash_token(token)
        await self.token_repo.create_refresh_token(
            jti=jti,
            user_id=user_id,
            token_hash=token_hash,
            token_family_id=token_family_id,
            expires_at=datetime.now(timezone.utc) + self.refresh_token_expire,
            device_id=device_id
        )

        # Add token to family in Redis for fast lookup
        await self._add_token_to_family(token_family_id, jti)

        return token

    async def verify_token(
        self,
        token: str,
        token_type: str = "access"
    ) -> dict[str, Any]:
        """
        Verify and decode JWT token.

        EXPERT FIX: Uses public key for verification (separation of concerns).

        Args:
            token: JWT token string
            token_type: Expected token type ("access" or "refresh")

        Returns:
            Decoded token payload

        Raises:
            TokenExpiredError: Token has expired
            InvalidTokenError: Token is invalid or malformed
            TokenRevokedError: Token has been revoked
        """
        try:
            # Decode with public key (expert recommendation)
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[self.algorithm],
                audience=settings.JWT_AUDIENCE,
                issuer=settings.JWT_ISSUER,
                options={"verify_exp": True}
            )

            # Verify token type matches expected
            if payload.get("token_type") != token_type:
                raise InvalidTokenError(
                    f"Invalid token type. Expected {token_type}, got {payload.get('token_type')}"
                )

            # Check revocation status for access tokens
            if token_type == "access":
                jti = payload.get("jti")
                if await self._is_token_revoked(jti):
                    raise TokenRevokedError("Token has been revoked")

            return payload

        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Token validation failed: {str(e)}")
        except Exception as e:
            logger.error(f"token_verification_failed - {str(e)}")
            raise InvalidTokenError(f"Token verification failed: {str(e)}")

    async def rotate_refresh_token(
        self,
        old_refresh_token: str
    ) -> Tuple[str, str]:
        """
        Rotate refresh token and generate new access token.

        EXPERT FIX APPLIED:
        1. Extracts family ID (fid) from old token payload
        2. Detects token reuse and revokes entire family if reused
        3. Propagates original family ID to new refresh token
        4. Uses public key for token decoding

        Args:
            old_refresh_token: Current refresh token

        Returns:
            Tuple of (new_access_token, new_refresh_token)

        Raises:
            InvalidTokenError: Token is invalid
            TokenReuseError: Token reuse detected (security breach)
            TokenRevokedError: Token has been revoked
        """
        try:
            # Decode with public key (expert recommendation)
            payload = jwt.decode(
                old_refresh_token,
                self.public_key,
                algorithms=[self.algorithm],
                audience=settings.JWT_AUDIENCE,
                issuer=settings.JWT_ISSUER,
                options={"verify_exp": True}
            )

            jti = payload["jti"]
            user_id = UUID(payload["sub"])

            # Extract family ID (expert recommendation)
            family_id = payload.get("fid")
            if not family_id:
                # Old token without family tracking - reject for security
                raise InvalidTokenError("Refresh token is missing a family ID")

            device_id = payload.get("device_id")

            # Check if token was already used (REUSE DETECTION)
            if await self.token_repo.is_token_revoked(jti):
                # SECURITY BREACH: Token reuse detected!
                logger.warning(f"token_reuse_detected - user_id={user_id}, family_id={family_id}, jti={jti}")
                await self._revoke_token_family(family_id)
                raise TokenReuseError("Attempted to reuse a revoked refresh token")

            # Revoke the old token now that it's been used (one-time use)
            await self.token_repo.revoke_token(jti)

            # Get user data for new access token
            user = await self.token_repo.get_user(user_id)
            if not user:
                raise InvalidTokenError("User not found")

            # Generate new access token
            new_access_token, _ = await self.create_access_token(
                user_id=user.id,
                email=user.email,
                role=user.role,
                company_id=None,  # TODO: Get from user_companies
                permissions=[]  # TODO: Get from role
            )

            # Generate new refresh token - PROPAGATE FAMILY ID (expert fix)
            new_refresh_token = await self.create_refresh_token(
                user_id=user_id,
                token_family_id=family_id,  # CRITICAL: Use original family ID
                device_id=device_id
            )

            return new_access_token, new_refresh_token

        except (jwt.PyJWTError, KeyError) as e:
            raise InvalidTokenError(f"Invalid refresh token: {str(e)}")

    async def revoke_token(self, jti: str) -> None:
        """
        Revoke a single token by JTI.

        Args:
            jti: Token unique identifier
        """
        # Mark as revoked in cache
        cache_key = f"token:{jti}"
        cached = await redis_client.get(cache_key)
        if cached:
            metadata = json.loads(cached)
            metadata["valid"] = False
            await redis_client.setex(
                cache_key,
                await redis_client.ttl(cache_key),
                json.dumps(metadata)
            )

        # Add to revocation list
        revoke_key = f"revoked:{jti}"
        await redis_client.setex(
            revoke_key,
            86400 * 7,  # Keep for 7 days
            "1"
        )

    async def _revoke_token_family(self, family_id: str) -> None:
        """
        Revoke all tokens in a family (security breach response).

        Args:
            family_id: Token family identifier
        """
        # Get all tokens in family from Redis
        family_key = f"token_family:{family_id}"
        token_ids = await redis_client.smembers(family_key)

        # Revoke each token
        for jti in token_ids:
            await self.revoke_token(jti)

        # Clear the family
        await redis_client.delete(family_key)

        # Revoke in database
        await self.token_repo.revoke_family(family_id)

        logger.warning(f"token_family_revoked - family_id={family_id}, token_count={len(token_ids)}")

    async def _add_token_to_family(self, family_id: str, jti: str) -> None:
        """Add token to family set in Redis."""
        family_key = f"token_family:{family_id}"
        await redis_client.sadd(family_key, jti)
        await redis_client.expire(family_key, int(self.refresh_token_expire.total_seconds()))

    async def _is_token_revoked(self, jti: str) -> bool:
        """Check if token is revoked in Redis."""
        revoke_key = f"revoked:{jti}"
        return await redis_client.exists(revoke_key) > 0

    def _hash_token(self, token: str) -> str:
        """Hash token for secure storage using SHA-256."""
        return hashlib.sha256(token.encode()).hexdigest()
