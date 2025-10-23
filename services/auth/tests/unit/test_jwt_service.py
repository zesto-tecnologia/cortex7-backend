"""Unit tests for JWT Service."""

import pytest
from uuid import uuid4, UUID
from datetime import datetime, timedelta
import jwt as pyjwt

from services.auth.services.jwt_service import JWTService
from services.auth.core.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
    TokenRevokedError,
    TokenReuseError
)
from services.auth.models.user import User
from services.auth.repositories.refresh_token_repository import RefreshTokenRepository
from services.auth.core.cache import RedisClient


@pytest.fixture
async def jwt_service(refresh_token_repo: RefreshTokenRepository, redis_client: RedisClient):
    """Create JWT service instance."""
    return JWTService(token_repo=refresh_token_repo, redis=redis_client)


class TestAccessTokenGeneration:
    """Test access token generation."""

    @pytest.mark.asyncio
    async def test_create_access_token_basic(self, jwt_service: JWTService, test_user: User):
        """Test basic access token generation."""
        token, payload = await jwt_service.create_access_token(
            user_id=test_user.id,
            email=test_user.email,
            role=test_user.role
        )

        assert isinstance(token, str)
        assert isinstance(payload, dict)
        assert payload["sub"] == str(test_user.id)
        assert payload["email"] == test_user.email
        assert payload["role"] == test_user.role
        assert payload["token_type"] == "access"
        assert "jti" in payload
        assert "exp" in payload
        assert "iat" in payload

    @pytest.mark.asyncio
    async def test_access_token_expiration(self, jwt_service: JWTService, test_user: User):
        """Test access token has correct expiration."""
        token, payload = await jwt_service.create_access_token(
            user_id=test_user.id,
            email=test_user.email,
            role=test_user.role
        )

        exp = datetime.fromtimestamp(payload["exp"])
        iat = datetime.fromtimestamp(payload["iat"])
        diff = exp - iat

        # Should expire in ~10 minutes (600 seconds)
        assert 590 <= diff.total_seconds() <= 610

    @pytest.mark.asyncio
    async def test_access_token_with_permissions(self, jwt_service: JWTService, admin_user: User):
        """Test access token with custom permissions."""
        permissions = ["read:users", "write:users", "delete:users"]

        token, payload = await jwt_service.create_access_token(
            user_id=admin_user.id,
            email=admin_user.email,
            role=admin_user.role,
            permissions=permissions
        )

        assert payload["permissions"] == permissions

    @pytest.mark.asyncio
    async def test_access_token_with_company_id(self, jwt_service: JWTService, test_user: User):
        """Test access token with company_id."""
        company_id = uuid4()

        token, payload = await jwt_service.create_access_token(
            user_id=test_user.id,
            email=test_user.email,
            role=test_user.role,
            company_id=company_id
        )

        assert payload["company_id"] == str(company_id)


class TestRefreshTokenGeneration:
    """Test refresh token generation."""

    @pytest.mark.asyncio
    async def test_create_refresh_token_basic(self, jwt_service: JWTService, test_user: User, db_session):
        """Test basic refresh token generation."""
        token = await jwt_service.create_refresh_token(user_id=test_user.id)

        assert isinstance(token, str)

        # Verify token can be decoded
        payload = pyjwt.decode(
            token,
            jwt_service.public_key,
            algorithms=[jwt_service.algorithm]
        )

        assert payload["sub"] == str(test_user.id)
        assert payload["token_type"] == "refresh"
        assert "jti" in payload
        assert "fid" in payload  # Family ID should be present

        # Verify family ID equals JTI for first token
        assert payload["fid"] == payload["jti"]

    @pytest.mark.asyncio
    async def test_refresh_token_stored_in_db(
        self,
        jwt_service: JWTService,
        test_user: User,
        refresh_token_repo: RefreshTokenRepository,
        db_session
    ):
        """Test refresh token is stored in database."""
        token = await jwt_service.create_refresh_token(user_id=test_user.id)

        # Decode to get JTI
        payload = pyjwt.decode(
            token,
            jwt_service.public_key,
            algorithms=[jwt_service.algorithm],
            options={"verify_exp": False}
        )

        # Verify token exists in database
        tokens = await refresh_token_repo.get_user_tokens(test_user.id)
        assert len(tokens) == 1

    @pytest.mark.asyncio
    async def test_refresh_token_family_tracking(self, jwt_service: JWTService, test_user: User):
        """Test refresh token includes family ID."""
        family_id = str(uuid4())

        token = await jwt_service.create_refresh_token(
            user_id=test_user.id,
            token_family_id=family_id
        )

        payload = pyjwt.decode(
            token,
            jwt_service.public_key,
            algorithms=[jwt_service.algorithm]
        )

        # Family ID should match provided value (not JTI)
        assert payload["fid"] == family_id
        assert payload["fid"] != payload["jti"]

    @pytest.mark.asyncio
    async def test_refresh_token_device_tracking(self, jwt_service: JWTService, test_user: User):
        """Test refresh token with device ID."""
        device_id = "device-123"

        token = await jwt_service.create_refresh_token(
            user_id=test_user.id,
            device_id=device_id
        )

        payload = pyjwt.decode(
            token,
            jwt_service.public_key,
            algorithms=[jwt_service.algorithm]
        )

        assert payload.get("device_id") == device_id


class TestTokenVerification:
    """Test token verification."""

    @pytest.mark.asyncio
    async def test_verify_valid_access_token(self, jwt_service: JWTService, test_user: User):
        """Test verifying valid access token."""
        token, original_payload = await jwt_service.create_access_token(
            user_id=test_user.id,
            email=test_user.email,
            role=test_user.role
        )

        # Verify token
        payload = await jwt_service.verify_token(token, "access")

        assert payload["sub"] == original_payload["sub"]
        assert payload["email"] == original_payload["email"]
        assert payload["jti"] == original_payload["jti"]

    @pytest.mark.asyncio
    async def test_verify_malformed_token(self, jwt_service: JWTService):
        """Test verifying malformed token raises error."""
        with pytest.raises(InvalidTokenError):
            await jwt_service.verify_token("invalid.token.here", "access")

    @pytest.mark.asyncio
    async def test_verify_token_wrong_signature(self, jwt_service: JWTService, test_user: User):
        """Test token with wrong signature fails verification."""
        # Create token with different key
        fake_token = pyjwt.encode(
            {"sub": str(test_user.id), "email": test_user.email},
            "wrong-secret-key",
            algorithm="HS256"
        )

        with pytest.raises(InvalidTokenError):
            await jwt_service.verify_token(fake_token, "access")

    @pytest.mark.asyncio
    async def test_verify_revoked_token(
        self,
        jwt_service: JWTService,
        test_user: User,
        redis_client: RedisClient
    ):
        """Test verifying revoked token raises error."""
        token, payload = await jwt_service.create_access_token(
            user_id=test_user.id,
            email=test_user.email,
            role=test_user.role
        )

        # Revoke token
        await jwt_service.revoke_token(payload["jti"])

        # Verify raises TokenRevokedError
        with pytest.raises(TokenRevokedError):
            await jwt_service.verify_token(token, "access")


class TestTokenRotation:
    """Test refresh token rotation."""

    @pytest.mark.asyncio
    async def test_rotate_refresh_token_success(
        self,
        jwt_service: JWTService,
        test_user: User,
        refresh_token_repo: RefreshTokenRepository,
        db_session
    ):
        """Test successful refresh token rotation."""
        # Create initial refresh token
        old_token = await jwt_service.create_refresh_token(user_id=test_user.id)

        # Rotate token
        new_access_token, new_refresh_token = await jwt_service.rotate_refresh_token(old_token)

        # Verify new tokens are different
        assert old_token != new_refresh_token
        assert isinstance(new_access_token, str)
        assert isinstance(new_refresh_token, str)

        # Decode tokens to check family preservation
        old_payload = pyjwt.decode(
            old_token,
            jwt_service.public_key,
            algorithms=[jwt_service.algorithm],
            options={"verify_exp": False}
        )

        new_payload = pyjwt.decode(
            new_refresh_token,
            jwt_service.public_key,
            algorithms=[jwt_service.algorithm]
        )

        # Family ID should be preserved
        assert old_payload["fid"] == new_payload["fid"]

        # JTI should be different
        assert old_payload["jti"] != new_payload["jti"]

    @pytest.mark.asyncio
    async def test_old_token_revoked_after_rotation(
        self,
        jwt_service: JWTService,
        test_user: User,
        refresh_token_repo: RefreshTokenRepository,
        db_session
    ):
        """Test old token is revoked after rotation."""
        old_token = await jwt_service.create_refresh_token(user_id=test_user.id)

        # Get JTI from old token
        old_payload = pyjwt.decode(
            old_token,
            jwt_service.public_key,
            algorithms=[jwt_service.algorithm],
            options={"verify_exp": False}
        )

        # Rotate
        await jwt_service.rotate_refresh_token(old_token)

        # Verify old token is revoked
        is_revoked = await refresh_token_repo.is_token_revoked(old_payload["jti"])
        assert is_revoked is True


class TestTokenReuseDetection:
    """Test token reuse detection and family revocation."""

    @pytest.mark.asyncio
    async def test_reuse_detection_revokes_family(
        self,
        jwt_service: JWTService,
        test_user: User,
        refresh_token_repo: RefreshTokenRepository,
        redis_client: RedisClient,
        db_session
    ):
        """Test that reusing a token revokes entire family."""
        # Create initial token
        token1 = await jwt_service.create_refresh_token(user_id=test_user.id)

        # Rotate to token2
        _, token2 = await jwt_service.rotate_refresh_token(token1)

        # Try to reuse token1 (should trigger family revocation)
        with pytest.raises(TokenReuseError):
            await jwt_service.rotate_refresh_token(token1)

        # Verify token2 is also revoked (family revocation)
        token2_payload = pyjwt.decode(
            token2,
            jwt_service.public_key,
            algorithms=[jwt_service.algorithm],
            options={"verify_exp": False}
        )

        is_revoked = await refresh_token_repo.is_token_revoked(token2_payload["jti"])
        assert is_revoked is True

    @pytest.mark.asyncio
    async def test_family_revocation_count(
        self,
        jwt_service: JWTService,
        test_user: User,
        refresh_token_repo: RefreshTokenRepository,
        db_session
    ):
        """Test family revocation revokes all tokens in family."""
        # Create chain of tokens
        token1 = await jwt_service.create_refresh_token(user_id=test_user.id)
        _, token2 = await jwt_service.rotate_refresh_token(token1)
        _, token3 = await jwt_service.rotate_refresh_token(token2)

        # Get family ID
        payload = pyjwt.decode(
            token3,
            jwt_service.public_key,
            algorithms=[jwt_service.algorithm],
            options={"verify_exp": False}
        )
        family_id = payload["fid"]

        # Revoke family
        count = await refresh_token_repo.revoke_family(family_id)

        # All non-revoked tokens in family should be revoked
        # token1 was already revoked during rotation, so count should be for token2 and token3
        assert count >= 1  # At least token3 should be revoked


class TestTokenRevocation:
    """Test manual token revocation."""

    @pytest.mark.asyncio
    async def test_revoke_access_token(
        self,
        jwt_service: JWTService,
        test_user: User,
        redis_client: RedisClient
    ):
        """Test manually revoking an access token."""
        token, payload = await jwt_service.create_access_token(
            user_id=test_user.id,
            email=test_user.email,
            role=test_user.role
        )

        # Revoke token
        await jwt_service.revoke_token(payload["jti"])

        # Verify token is revoked
        is_revoked = await jwt_service._is_token_revoked(payload["jti"])
        assert is_revoked is True

    @pytest.mark.asyncio
    async def test_revoke_refresh_token(
        self,
        jwt_service: JWTService,
        test_user: User,
        refresh_token_repo: RefreshTokenRepository,
        db_session
    ):
        """Test manually revoking a refresh token."""
        token = await jwt_service.create_refresh_token(user_id=test_user.id)

        payload = pyjwt.decode(
            token,
            jwt_service.public_key,
            algorithms=[jwt_service.algorithm],
            options={"verify_exp": False}
        )

        # Revoke token
        await jwt_service.revoke_token(payload["jti"])

        # Verify token is revoked in DB
        is_revoked = await refresh_token_repo.is_token_revoked(payload["jti"])
        assert is_revoked is True
