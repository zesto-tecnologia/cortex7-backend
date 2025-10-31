"""Tests for cortex_auth.models module."""

import pytest
from cortex_auth.models import TokenPayload, User


class TestUser:
    """Test User model functionality."""

    def test_user_creation(self, mock_user):
        """Test User instance creation."""
        assert mock_user.user_id == "123e4567-e89b-12d3-a456-426614174000"
        assert mock_user.email == "test@example.com"
        assert mock_user.name == "Test User"
        assert "user" in mock_user.roles
        assert "manager" in mock_user.roles

    def test_has_role(self, mock_user):
        """Test has_role method."""
        assert mock_user.has_role("user") is True
        assert mock_user.has_role("manager") is True
        assert mock_user.has_role("admin") is False

    def test_has_any_role(self, mock_user, admin_user, basic_user):
        """Test has_any_role method."""
        assert mock_user.has_any_role(["admin", "manager"]) is True
        assert basic_user.has_any_role(["admin", "manager"]) is False
        assert admin_user.has_any_role(["admin"]) is True

    def test_has_all_roles(self, mock_user, admin_user):
        """Test has_all_roles method."""
        assert mock_user.has_all_roles(["user", "manager"]) is True
        assert mock_user.has_all_roles(["user", "admin"]) is False
        assert admin_user.has_all_roles(["admin", "user"]) is True

    def test_has_permission(self, mock_user, admin_user):
        """Test has_permission method with direct and wildcard permissions."""
        # Direct permission
        assert mock_user.has_permission("read:documents") is True
        assert mock_user.has_permission("delete:documents") is False

        # Wildcard permission (*:reports allows any action on reports)
        assert mock_user.has_permission("read:reports") is True
        assert mock_user.has_permission("write:reports") is True
        assert mock_user.has_permission("delete:reports") is True

        # Admin with *:* permission
        assert admin_user.has_permission("anything:anywhere") is True

    def test_has_all_permissions(self, mock_user):
        """Test has_all_permissions method."""
        assert mock_user.has_all_permissions(["read:documents", "write:documents"]) is True
        assert mock_user.has_all_permissions(["read:documents", "delete:documents"]) is False
        assert mock_user.has_all_permissions(["read:reports", "write:reports"]) is True

    def test_from_token_payload(self, valid_token_payload):
        """Test creating User from token payload."""
        user = User.from_token_payload(valid_token_payload)
        assert user.user_id == valid_token_payload["user_id"]
        assert user.email == valid_token_payload["email"]
        assert user.name == valid_token_payload["name"]
        assert user.roles == valid_token_payload["roles"]
        assert user.permissions == valid_token_payload["permissions"]


class TestTokenPayload:
    """Test TokenPayload model functionality."""

    def test_token_payload_creation(self, valid_token_payload):
        """Test TokenPayload instance creation."""
        payload = TokenPayload(**valid_token_payload)
        assert payload.user_id == valid_token_payload["user_id"]
        assert payload.email == valid_token_payload["email"]
        assert payload.iss == "cortex-auth-service"
        assert payload.jti == valid_token_payload["jti"]
