"""Unit tests for Token Introspection Service."""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
import jwt as pyjwt

from services.auth.services.jwt_service import JWTService
from services.auth.services.token_introspection import TokenIntrospectionService
from services.auth.models.user import User
from services.auth.repositories.refresh_token_repository import RefreshTokenRepository
from services.auth.core.cache import RedisClient


@pytest.fixture
async def jwt_service(refresh_token_repo: RefreshTokenRepository, redis_client: RedisClient):
    """Create JWT service instance."""
    return JWTService(token_repo=refresh_token_repo, redis=redis_client)


@pytest.fixture
def introspection_service(jwt_service: JWTService):
    """Create token introspection service instance."""
    return TokenIntrospectionService(jwt_service=jwt_service)


class TestTokenIntrospection:
    """Test token introspection functionality."""

    @pytest.mark.asyncio
    async def test_introspect_valid_access_token(
        self,
        introspection_service: TokenIntrospectionService,
        jwt_service: JWTService,
        test_user: User
    ):
        """Test introspecting a valid access token."""
        permissions = ["read:profile", "update:profile"]

        token, _ = await jwt_service.create_access_token(
            user_id=test_user.id,
            email=test_user.email,
            role=test_user.role,
            permissions=permissions
        )

        # Introspect token
        result = await introspection_service.introspect(token, token_type_hint="access")

        # Verify RFC 7662 compliant response
        assert result["active"] is True
        assert result["username"] == test_user.email
        assert result["scope"] == " ".join(permissions)
        assert result["token_type"] == "access"
        assert "exp" in result
        assert "iat" in result
        assert "sub" in result
        assert "jti" in result

    @pytest.mark.asyncio
    async def test_introspect_valid_refresh_token(
        self,
        introspection_service: TokenIntrospectionService,
        jwt_service: JWTService,
        test_user: User
    ):
        """Test introspecting a valid refresh token."""
        token = await jwt_service.create_refresh_token(user_id=test_user.id)

        result = await introspection_service.introspect(token, token_type_hint="refresh")

        assert result["active"] is True
        assert result["token_type"] == "refresh"
        assert result["sub"] == str(test_user.id)

    @pytest.mark.asyncio
    async def test_introspect_expired_token(
        self,
        introspection_service: TokenIntrospectionService,
        jwt_service: JWTService,
        test_user: User
    ):
        """Test introspecting an expired token returns inactive."""
        # Create token that's already expired
        expired_token = pyjwt.encode(
            {
                "sub": str(test_user.id),
                "email": test_user.email,
                "token_type": "access",
                "exp": datetime.utcnow() - timedelta(hours=1),  # Expired
                "iat": datetime.utcnow() - timedelta(hours=2),
                "jti": str(uuid4())
            },
            jwt_service.private_key,
            algorithm=jwt_service.algorithm
        )

        result = await introspection_service.introspect(expired_token)

        assert result["active"] is False

    @pytest.mark.asyncio
    async def test_introspect_revoked_token(
        self,
        introspection_service: TokenIntrospectionService,
        jwt_service: JWTService,
        test_user: User
    ):
        """Test introspecting a revoked token returns inactive."""
        token, payload = await jwt_service.create_access_token(
            user_id=test_user.id,
            email=test_user.email,
            role=test_user.role
        )

        # Revoke token
        await jwt_service.revoke_token(payload["jti"])

        result = await introspection_service.introspect(token)

        assert result["active"] is False

    @pytest.mark.asyncio
    async def test_introspect_malformed_token(
        self,
        introspection_service: TokenIntrospectionService
    ):
        """Test introspecting a malformed token returns inactive."""
        result = await introspection_service.introspect("invalid.token.here")

        assert result["active"] is False

    @pytest.mark.asyncio
    async def test_introspect_includes_custom_claims(
        self,
        introspection_service: TokenIntrospectionService,
        jwt_service: JWTService,
        admin_user: User
    ):
        """Test introspection includes custom claims."""
        company_id = uuid4()

        token, _ = await jwt_service.create_access_token(
            user_id=admin_user.id,
            email=admin_user.email,
            role=admin_user.role,
            company_id=company_id
        )

        result = await introspection_service.introspect(token)

        assert result["active"] is True
        assert result["role"] == "admin"
        assert result["email"] == admin_user.email
        assert result["company_id"] == str(company_id)


class TestTokenRevocation:
    """Test token revocation via introspection service."""

    @pytest.mark.asyncio
    async def test_revoke_valid_token(
        self,
        introspection_service: TokenIntrospectionService,
        jwt_service: JWTService,
        test_user: User
    ):
        """Test revoking a valid token."""
        token, payload = await jwt_service.create_access_token(
            user_id=test_user.id,
            email=test_user.email,
            role=test_user.role
        )

        # Revoke token
        result = await introspection_service.revoke_token(token)

        assert result is True

        # Verify token is now inactive
        introspection = await introspection_service.introspect(token)
        assert introspection["active"] is False

    @pytest.mark.asyncio
    async def test_revoke_expired_token(
        self,
        introspection_service: TokenIntrospectionService,
        jwt_service: JWTService,
        test_user: User
    ):
        """Test revoking an expired token (should still work for security)."""
        # Create expired token
        expired_token = pyjwt.encode(
            {
                "sub": str(test_user.id),
                "email": test_user.email,
                "token_type": "access",
                "exp": datetime.utcnow() - timedelta(hours=1),
                "iat": datetime.utcnow() - timedelta(hours=2),
                "jti": str(uuid4())
            },
            jwt_service.private_key,
            algorithm=jwt_service.algorithm
        )

        # Should still allow revocation
        result = await introspection_service.revoke_token(expired_token)

        assert result is True

    @pytest.mark.asyncio
    async def test_revoke_token_without_jti(
        self,
        introspection_service: TokenIntrospectionService,
        jwt_service: JWTService,
        test_user: User
    ):
        """Test revoking a token without JTI fails gracefully."""
        # Create token without JTI
        token_without_jti = pyjwt.encode(
            {
                "sub": str(test_user.id),
                "email": test_user.email,
                "exp": datetime.utcnow() + timedelta(hours=1),
            },
            jwt_service.private_key,
            algorithm=jwt_service.algorithm
        )

        result = await introspection_service.revoke_token(token_without_jti)

        assert result is False


class TestGetTokenInfo:
    """Test getting detailed token information."""

    @pytest.mark.asyncio
    async def test_get_token_info_valid_token(
        self,
        introspection_service: TokenIntrospectionService,
        jwt_service: JWTService,
        test_user: User
    ):
        """Test getting detailed info for valid token."""
        token, original_payload = await jwt_service.create_access_token(
            user_id=test_user.id,
            email=test_user.email,
            role=test_user.role
        )

        info = await introspection_service.get_token_info(token)

        assert info["valid"] is True
        assert info["is_expired"] is False
        assert info["is_revoked"] is False
        assert info["payload"]["sub"] == str(test_user.id)
        assert info["payload"]["email"] == test_user.email
        assert "expires_at" in info
        assert "issued_at" in info

    @pytest.mark.asyncio
    async def test_get_token_info_expired_token(
        self,
        introspection_service: TokenIntrospectionService,
        jwt_service: JWTService,
        test_user: User
    ):
        """Test getting info for expired token."""
        expired_token = pyjwt.encode(
            {
                "sub": str(test_user.id),
                "email": test_user.email,
                "token_type": "access",
                "exp": datetime.utcnow() - timedelta(hours=1),
                "iat": datetime.utcnow() - timedelta(hours=2),
                "jti": str(uuid4())
            },
            jwt_service.private_key,
            algorithm=jwt_service.algorithm
        )

        info = await introspection_service.get_token_info(expired_token)

        assert info["valid"] is False
        assert info["is_expired"] is True
        assert info["is_revoked"] is False

    @pytest.mark.asyncio
    async def test_get_token_info_revoked_token(
        self,
        introspection_service: TokenIntrospectionService,
        jwt_service: JWTService,
        test_user: User
    ):
        """Test getting info for revoked token."""
        token, payload = await jwt_service.create_access_token(
            user_id=test_user.id,
            email=test_user.email,
            role=test_user.role
        )

        # Revoke token
        await jwt_service.revoke_token(payload["jti"])

        info = await introspection_service.get_token_info(token)

        assert info["valid"] is False
        assert info["is_expired"] is False
        assert info["is_revoked"] is True

    @pytest.mark.asyncio
    async def test_get_token_info_invalid_token(
        self,
        introspection_service: TokenIntrospectionService
    ):
        """Test getting info for invalid token."""
        info = await introspection_service.get_token_info("invalid.token.here")

        assert info["valid"] is False
        assert "error" in info
