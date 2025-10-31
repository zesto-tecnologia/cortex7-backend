"""Unit tests for Kong Token Service."""

import pytest
from uuid import uuid4

from services.auth.services.jwt_service import JWTService
from services.auth.services.kong_token_service import KongTokenService
from services.auth.models.user import User
from services.auth.repositories.refresh_token_repository import RefreshTokenRepository
from services.auth.core.cache import RedisClient


@pytest.fixture
async def jwt_service(refresh_token_repo: RefreshTokenRepository, redis_client: RedisClient):
    """Create JWT service instance."""
    return JWTService(token_repo=refresh_token_repo, redis=redis_client)


@pytest.fixture
def kong_service(jwt_service: JWTService):
    """Create Kong token service instance."""
    return KongTokenService(jwt_service=jwt_service)


class TestRoleMapping:
    """Test role to Kong ACL group mapping."""

    def test_map_user_role(self, kong_service: KongTokenService):
        """Test mapping user role to ACL groups."""
        groups = kong_service._map_role_to_groups("user")

        assert "users" in groups
        assert "basic" in groups
        assert "admins" not in groups

    def test_map_admin_role(self, kong_service: KongTokenService):
        """Test mapping admin role to ACL groups."""
        groups = kong_service._map_role_to_groups("admin")

        assert "users" in groups
        assert "admins" in groups
        assert "basic" in groups
        assert "advanced" in groups
        assert "super_admins" not in groups

    def test_map_super_admin_role(self, kong_service: KongTokenService):
        """Test mapping super_admin role to ACL groups."""
        groups = kong_service._map_role_to_groups("super_admin")

        assert "users" in groups
        assert "admins" in groups
        assert "super_admins" in groups
        assert "basic" in groups
        assert "advanced" in groups
        assert "system" in groups

    def test_map_unknown_role(self, kong_service: KongTokenService):
        """Test mapping unknown role defaults to users."""
        groups = kong_service._map_role_to_groups("unknown_role")

        assert groups == ["users"]


class TestPermissionGeneration:
    """Test permission generation based on roles."""

    def test_generate_user_permissions(self, kong_service: KongTokenService):
        """Test generating permissions for user role."""
        permissions = kong_service._generate_permissions("user")

        assert "read:profile" in permissions
        assert "update:profile" in permissions
        assert "read:company" in permissions
        assert "create:users" not in permissions

    def test_generate_admin_permissions(self, kong_service: KongTokenService):
        """Test generating permissions for admin role."""
        permissions = kong_service._generate_permissions("admin")

        # Should have base permissions
        assert "read:profile" in permissions

        # Should have admin permissions
        assert "create:users" in permissions
        assert "read:users" in permissions
        assert "update:users" in permissions

        # Should not have super_admin permissions
        assert "delete:users" not in permissions
        assert "manage:roles" not in permissions

    def test_generate_super_admin_permissions(self, kong_service: KongTokenService):
        """Test generating permissions for super_admin role."""
        permissions = kong_service._generate_permissions("super_admin")

        # Should have all permissions
        assert "read:profile" in permissions
        assert "create:users" in permissions
        assert "delete:users" in permissions
        assert "manage:roles" in permissions
        assert "manage:companies" in permissions
        assert "manage:api_keys" in permissions

    def test_generate_unknown_role_permissions(self, kong_service: KongTokenService):
        """Test generating permissions for unknown role."""
        permissions = kong_service._generate_permissions("unknown")

        # Should get base permissions only
        assert "read:profile" in permissions
        assert "create:users" not in permissions


class TestRateLimitConfig:
    """Test rate limiting configuration."""

    def test_standard_rate_limits(self, kong_service: KongTokenService):
        """Test standard tier rate limits."""
        config = kong_service.get_rate_limit_config("standard")

        assert config["minute"] == 60
        assert config["hour"] == 1000
        assert config["day"] == 10000

    def test_premium_rate_limits(self, kong_service: KongTokenService):
        """Test premium tier rate limits."""
        config = kong_service.get_rate_limit_config("premium")

        assert config["minute"] == 200
        assert config["hour"] == 5000
        assert config["day"] == 50000

    def test_enterprise_rate_limits(self, kong_service: KongTokenService):
        """Test enterprise tier rate limits."""
        config = kong_service.get_rate_limit_config("enterprise")

        assert config["minute"] == 1000
        assert config["hour"] == 20000
        assert config["day"] == 200000

    def test_unknown_tier_defaults_to_standard(self, kong_service: KongTokenService):
        """Test unknown tier defaults to standard limits."""
        config = kong_service.get_rate_limit_config("unknown_tier")

        # Should match standard tier
        standard = kong_service.get_rate_limit_config("standard")
        assert config == standard


class TestKongTokenGeneration:
    """Test Kong-compatible token generation."""

    @pytest.mark.asyncio
    async def test_generate_kong_token_basic(
        self,
        kong_service: KongTokenService,
        test_user: User
    ):
        """Test generating basic Kong token."""
        token = await kong_service.generate_kong_token(
            user_id=test_user.id,
            email=test_user.email,
            role=test_user.role
        )

        assert isinstance(token, str)
        assert len(token) > 0

    @pytest.mark.asyncio
    async def test_generate_kong_token_with_company(
        self,
        kong_service: KongTokenService,
        test_user: User
    ):
        """Test generating Kong token with company ID."""
        company_id = uuid4()

        token = await kong_service.generate_kong_token(
            user_id=test_user.id,
            email=test_user.email,
            role=test_user.role,
            company_id=company_id
        )

        assert isinstance(token, str)

    @pytest.mark.asyncio
    async def test_generate_kong_token_with_rate_limit(
        self,
        kong_service: KongTokenService,
        admin_user: User
    ):
        """Test generating Kong token with custom rate limit tier."""
        token = await kong_service.generate_kong_token(
            user_id=admin_user.id,
            email=admin_user.email,
            role=admin_user.role,
            rate_limit_tier="premium"
        )

        assert isinstance(token, str)
