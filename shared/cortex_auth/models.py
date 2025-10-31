"""
Pydantic models for cortex-auth library.

This module defines the User and TokenPayload models used for JWT validation
and authentication state management across microservices.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class TokenPayload(BaseModel):
    """
    JWT token payload model.

    Represents the decoded JWT token claims after validation.
    """

    user_id: str = Field(..., description="User's UUID as string")
    email: EmailStr = Field(..., description="User's email address")
    name: str = Field(..., description="User's full name")
    roles: list[str] = Field(default_factory=list, description="User's assigned roles")
    permissions: list[str] = Field(default_factory=list, description="User's permissions")
    iss: str = Field(..., description="Token issuer (cortex-auth-service)")
    iat: datetime | int = Field(..., description="Issued at timestamp")
    exp: datetime | int = Field(..., description="Expiration timestamp")
    jti: str = Field(..., description="JWT ID for tracking")

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "name": "John Doe",
                "roles": ["user", "manager"],
                "permissions": ["read:documents", "write:documents"],
                "iss": "cortex-auth-service",
                "iat": 1234567890,
                "exp": 1234571490,
                "jti": "unique-token-id",
            }
        }
    }


class User(BaseModel):
    """
    Authenticated user model.

    Represents the current authenticated user in request context.
    This is attached to request.state.user after successful JWT validation.
    """

    user_id: UUID | str = Field(..., description="User's unique identifier")
    email: EmailStr = Field(..., description="User's email address")
    name: str = Field(..., description="User's full name")
    roles: list[str] = Field(default_factory=list, description="User's assigned roles")
    permissions: list[str] = Field(default_factory=list, description="User's permissions")

    @classmethod
    def from_token_payload(cls, payload: dict[str, Any]) -> "User":
        """
        Create User instance from JWT payload dictionary.

        Args:
            payload: Decoded JWT token payload

        Returns:
            User instance with data from token payload
        """
        return cls(
            user_id=payload["user_id"],
            email=payload["email"],
            name=payload["name"],
            roles=payload.get("roles", []),
            permissions=payload.get("permissions", []),
        )

    def has_role(self, role: str) -> bool:
        """
        Check if user has a specific role.

        Args:
            role: Role name to check

        Returns:
            True if user has the role, False otherwise
        """
        return role in self.roles

    def has_any_role(self, roles: list[str]) -> bool:
        """
        Check if user has any of the specified roles.

        Args:
            roles: List of role names to check

        Returns:
            True if user has at least one role, False otherwise
        """
        return any(role in self.roles for role in roles)

    def has_all_roles(self, roles: list[str]) -> bool:
        """
        Check if user has all specified roles.

        Args:
            roles: List of role names to check

        Returns:
            True if user has all roles, False otherwise
        """
        return all(role in self.roles for role in roles)

    def has_permission(self, permission: str) -> bool:
        """
        Check if user has a specific permission.

        Supports wildcard permissions:
        - "*:*" grants all permissions
        - "*:resource" grants all actions on resource

        Args:
            permission: Permission string in format "action:resource"

        Returns:
            True if user has the permission, False otherwise
        """
        # Check direct permission
        if permission in self.permissions:
            return True

        # Check wildcard permissions
        if "*:*" in self.permissions:
            return True

        # Check resource wildcard (e.g., "*:users" allows any action on users)
        if ":" in permission:
            _, resource = permission.split(":", 1)
            if f"*:{resource}" in self.permissions:
                return True

        return False

    def has_all_permissions(self, permissions: list[str]) -> bool:
        """
        Check if user has all specified permissions.

        Args:
            permissions: List of permission strings to check

        Returns:
            True if user has all permissions, False otherwise
        """
        return all(self.has_permission(perm) for perm in permissions)

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "name": "John Doe",
                "roles": ["user", "manager"],
                "permissions": ["read:documents", "write:documents", "*:reports"],
            }
        }
    }
