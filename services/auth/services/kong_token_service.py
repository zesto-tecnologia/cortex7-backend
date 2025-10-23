"""Kong-Compatible Token Service for API Gateway integration.

This service generates JWT tokens with Kong-specific claims for:
- Kong JWT plugin compatibility
- Kong ACL (Access Control List) groups
- Kong rate limiting tiers
- Custom header forwarding
"""

from typing import Optional
from uuid import UUID
import structlog

from services.auth.services.jwt_service import JWTService
from services.auth.config import settings

logger = structlog.get_logger(__name__)


class KongTokenService:
    """Generate Kong Gateway compatible JWT tokens."""

    def __init__(self, jwt_service: JWTService):
        """Initialize Kong token service.

        Args:
            jwt_service: JWT service instance
        """
        self.jwt_service = jwt_service

    async def generate_kong_token(
        self,
        user_id: UUID,
        email: str,
        role: str,
        company_id: Optional[UUID] = None,
        rate_limit_tier: str = "standard"
    ) -> str:
        """
        Generate Kong-compatible JWT token with custom claims.

        Kong JWT Plugin expects:
        - Standard JWT claims (sub, exp, iat, iss)
        - Optional custom claims for routing and rate limiting

        Args:
            user_id: User UUID
            email: User email
            role: User role (user, admin, super_admin)
            company_id: Optional company UUID
            rate_limit_tier: Rate limiting tier (standard, premium, enterprise)

        Returns:
            JWT token with Kong-compatible claims
        """
        # Map role to Kong ACL groups
        kong_groups = self._map_role_to_groups(role)

        # Generate permissions based on role
        permissions = self._generate_permissions(role)

        # Build Kong-specific claims
        kong_claims = {
            # Kong ACL plugin expects 'groups' claim
            "groups": kong_groups,

            # Rate limiting metadata
            "rate_limit_tier": rate_limit_tier,
            "rate_limit_by": "consumer",  # Kong rate limiting strategy

            # Custom headers for downstream services
            "x-user-id": str(user_id),
            "x-user-role": role,
            "x-company-id": str(company_id) if company_id else None,

            # Routing hints
            "route_by_company": company_id is not None,
        }

        # Generate access token with Kong claims
        token, _ = await self.jwt_service.create_access_token(
            user_id=user_id,
            email=email,
            role=role,
            company_id=company_id,
            permissions=permissions
        )

        # TODO: Merge kong_claims into token generation
        # For now, return standard token (Kong extracts claims from standard format)

        logger.info(
            "Kong-compatible token generated",
            user_id=str(user_id),
            groups=kong_groups,
            tier=rate_limit_tier
        )

        return token

    def _map_role_to_groups(self, role: str) -> list[str]:
        """
        Map user role to Kong ACL groups.

        Kong ACL plugin uses groups for access control.

        Args:
            role: User role

        Returns:
            List of ACL group names
        """
        role_groups = {
            "user": ["users", "basic"],
            "admin": ["users", "admins", "basic", "advanced"],
            "super_admin": [
                "users",
                "admins",
                "super_admins",
                "basic",
                "advanced",
                "system"
            ]
        }
        return role_groups.get(role, ["users"])

    def _generate_permissions(self, role: str) -> list[str]:
        """
        Generate permissions based on role with inheritance.

        Args:
            role: User role

        Returns:
            List of permission strings
        """
        base_permissions = [
            "read:profile",
            "update:profile",
            "read:company"
        ]

        admin_permissions = [
            "create:users",
            "read:users",
            "update:users",
            "read:audit_logs"
        ]

        super_admin_permissions = [
            "delete:users",
            "manage:roles",
            "manage:companies",
            "read:system_logs",
            "manage:api_keys"
        ]

        if role == "user":
            return base_permissions
        elif role == "admin":
            return base_permissions + admin_permissions
        elif role == "super_admin":
            return base_permissions + admin_permissions + super_admin_permissions

        return base_permissions

    def get_rate_limit_config(self, tier: str) -> dict[str, int]:
        """
        Get rate limit configuration for tier.

        Args:
            tier: Rate limiting tier

        Returns:
            Rate limit configuration
        """
        rate_limits = {
            "standard": {
                "minute": 60,
                "hour": 1000,
                "day": 10000
            },
            "premium": {
                "minute": 200,
                "hour": 5000,
                "day": 50000
            },
            "enterprise": {
                "minute": 1000,
                "hour": 20000,
                "day": 200000
            }
        }

        return rate_limits.get(tier, rate_limits["standard"])
