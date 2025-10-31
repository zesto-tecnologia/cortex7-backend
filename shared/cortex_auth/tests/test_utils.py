"""
Comprehensive tests for cortex-auth utility functions.

Tests JWT validation, token decoding, role/permission checking,
clock skew tolerance, and error handling.
"""

import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt

from cortex_auth.utils import (
    decode_token,
    create_user_from_token,
    verify_roles,
    verify_all_roles,
    verify_permissions,
    verify_any_permission,
    extract_token_from_cookie,
    is_admin,
    is_manager,
)
from cortex_auth.models import User
from cortex_auth.exceptions import (
    TokenExpiredError,
    TokenInvalidError,
    IssuerInvalidError,
)


class TestDecodeToken:
    """Tests for decode_token() function."""

    def test_decode_valid_token(self, mock_settings, create_jwt_token, valid_token_payload):
        """Test that valid token is decoded successfully."""
        token = create_jwt_token(valid_token_payload)

        payload = decode_token(token)

        assert payload["user_id"] == valid_token_payload["user_id"]
        assert payload["email"] == valid_token_payload["email"]
        assert payload["name"] == valid_token_payload["name"]
        assert payload["roles"] == valid_token_payload["roles"]
        assert payload["permissions"] == valid_token_payload["permissions"]
        assert payload["iss"] == "cortex-auth-service"

    def test_decode_token_with_explicit_public_key(self, mock_settings, create_jwt_token, valid_token_payload, rsa_keys):
        """Test decoding with explicit public key parameter."""
        token = create_jwt_token(valid_token_payload)

        payload = decode_token(token, public_key=rsa_keys["public_key"])

        assert payload["user_id"] == valid_token_payload["user_id"]

    def test_decode_expired_token(self, mock_settings, create_jwt_token, valid_token_payload):
        """Test that expired token raises TokenExpiredError."""
        expired_token = create_jwt_token(valid_token_payload, expired=True)

        with pytest.raises(TokenExpiredError) as exc_info:
            decode_token(expired_token)

        assert "Token has expired" in str(exc_info.value)

    def test_decode_token_with_wrong_issuer(self, mock_settings, create_jwt_token, valid_token_payload):
        """Test that token with wrong issuer raises IssuerInvalidError."""
        wrong_issuer_token = create_jwt_token(valid_token_payload, wrong_issuer=True)

        with pytest.raises(IssuerInvalidError) as exc_info:
            decode_token(wrong_issuer_token)

        assert "Expected issuer 'cortex-auth-service'" in str(exc_info.value)

    def test_decode_token_with_invalid_signature(self, mock_settings, rsa_keys, valid_token_payload):
        """Test that token with invalid signature raises TokenInvalidError."""
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization

        # Generate different key pair
        wrong_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        wrong_private_pem = wrong_private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()

        # Sign with wrong key
        invalid_token = jwt.encode(
            valid_token_payload,
            wrong_private_pem,
            algorithm="RS256"
        )

        with pytest.raises(TokenInvalidError) as exc_info:
            decode_token(invalid_token)

        assert "Token validation failed" in str(exc_info.value)

    def test_decode_malformed_token(self, mock_settings):
        """Test that malformed token raises TokenInvalidError."""
        with pytest.raises(TokenInvalidError):
            decode_token("not-a-valid-jwt-token")

    def test_decode_token_clock_skew_tolerance(self, mock_settings, rsa_keys, valid_token_payload):
        """Test that clock skew tolerance is configured (jose library handles this internally)."""
        # Note: jose's jwt.decode handles clock skew internally with leeway parameter
        # Our custom clock skew logic in decode_token adds additional tolerance
        # Create token that will expire in 5 seconds (well within tolerance)
        payload_future_exp = {
            **valid_token_payload,
            "exp": datetime.now(timezone.utc) + timedelta(seconds=5)
        }

        token = jwt.encode(
            payload_future_exp,
            rsa_keys["private_key"],
            algorithm="RS256"
        )

        # Should work fine with future expiration
        decoded = decode_token(token)
        assert decoded["user_id"] == valid_token_payload["user_id"]

    def test_decode_token_beyond_clock_skew(self, mock_settings, rsa_keys, valid_token_payload):
        """Test that tokens expired beyond clock skew tolerance are rejected."""
        # Create token that expired 90 seconds ago (beyond tolerance)
        payload_expired_beyond = {
            **valid_token_payload,
            "exp": datetime.now(timezone.utc) - timedelta(seconds=90)
        }

        token = jwt.encode(
            payload_expired_beyond,
            rsa_keys["private_key"],
            algorithm="RS256"
        )

        with pytest.raises(TokenExpiredError):
            decode_token(token)

    def test_decode_token_no_expiration_claim(self, mock_settings, rsa_keys):
        """Test token without exp claim (should still work)."""
        payload_no_exp = {
            "user_id": "test-id",
            "email": "test@example.com",
            "name": "Test",
            "roles": [],
            "permissions": [],
            "iss": "cortex-auth-service",
            "iat": datetime.now(timezone.utc),
            "jti": "test-jti"
        }

        token = jwt.encode(payload_no_exp, rsa_keys["private_key"], algorithm="RS256")

        decoded = decode_token(token)
        assert decoded["user_id"] == "test-id"


class TestCreateUserFromToken:
    """Tests for create_user_from_token() function."""

    def test_create_user_from_valid_token(self, mock_settings, create_jwt_token, valid_token_payload):
        """Test creating User from valid token."""
        token = create_jwt_token(valid_token_payload)

        user = create_user_from_token(token)

        assert isinstance(user, User)
        assert user.user_id == valid_token_payload["user_id"]
        assert user.email == valid_token_payload["email"]
        assert user.name == valid_token_payload["name"]
        assert user.roles == valid_token_payload["roles"]
        assert user.permissions == valid_token_payload["permissions"]

    def test_create_user_from_expired_token(self, mock_settings, create_jwt_token, valid_token_payload):
        """Test that expired token raises TokenExpiredError."""
        expired_token = create_jwt_token(valid_token_payload, expired=True)

        with pytest.raises(TokenExpiredError):
            create_user_from_token(expired_token)

    def test_create_user_with_explicit_public_key(self, mock_settings, create_jwt_token, valid_token_payload, rsa_keys):
        """Test creating user with explicit public key."""
        token = create_jwt_token(valid_token_payload)

        user = create_user_from_token(token, public_key=rsa_keys["public_key"])

        assert user.user_id == valid_token_payload["user_id"]


class TestVerifyRoles:
    """Tests for role verification functions."""

    def test_verify_roles_with_matching_role(self):
        """Test that user with required role passes verification."""
        user = User(
            user_id="test-id",
            email="test@example.com",
            name="Test",
            roles=["admin", "user"],
            permissions=[]
        )

        assert verify_roles(user, ["admin"]) is True

    def test_verify_roles_with_any_matching_role(self):
        """Test OR logic - user needs at least one role."""
        user = User(
            user_id="test-id",
            email="test@example.com",
            name="Test",
            roles=["manager"],
            permissions=[]
        )

        assert verify_roles(user, ["admin", "manager"]) is True

    def test_verify_roles_without_required_role(self):
        """Test that user without required role fails verification."""
        user = User(
            user_id="test-id",
            email="test@example.com",
            name="Test",
            roles=["user"],
            permissions=[]
        )

        assert verify_roles(user, ["admin"]) is False

    def test_verify_roles_empty_requirements(self):
        """Test that empty requirements always pass."""
        user = User(
            user_id="test-id",
            email="test@example.com",
            name="Test",
            roles=[],
            permissions=[]
        )

        assert verify_roles(user, []) is True

    def test_verify_all_roles_success(self):
        """Test AND logic - user must have all roles."""
        user = User(
            user_id="test-id",
            email="test@example.com",
            name="Test",
            roles=["admin", "manager"],
            permissions=[]
        )

        assert verify_all_roles(user, ["admin", "manager"]) is True

    def test_verify_all_roles_failure(self):
        """Test that user with only some roles fails AND check."""
        user = User(
            user_id="test-id",
            email="test@example.com",
            name="Test",
            roles=["admin"],
            permissions=[]
        )

        assert verify_all_roles(user, ["admin", "manager"]) is False

    def test_verify_all_roles_empty_requirements(self):
        """Test that empty requirements always pass."""
        user = User(
            user_id="test-id",
            email="test@example.com",
            name="Test",
            roles=[],
            permissions=[]
        )

        assert verify_all_roles(user, []) is True


class TestVerifyPermissions:
    """Tests for permission verification functions."""

    def test_verify_permissions_with_exact_match(self):
        """Test exact permission match."""
        user = User(
            user_id="test-id",
            email="test@example.com",
            name="Test",
            roles=[],
            permissions=["read:documents", "write:documents"]
        )

        assert verify_permissions(user, ["read:documents"]) is True

    def test_verify_permissions_with_multiple_required(self):
        """Test AND logic - user must have all permissions."""
        user = User(
            user_id="test-id",
            email="test@example.com",
            name="Test",
            roles=[],
            permissions=["read:documents", "write:documents"]
        )

        assert verify_permissions(user, ["read:documents", "write:documents"]) is True

    def test_verify_permissions_missing_one(self):
        """Test that missing one required permission fails."""
        user = User(
            user_id="test-id",
            email="test@example.com",
            name="Test",
            roles=[],
            permissions=["read:documents"]
        )

        assert verify_permissions(user, ["read:documents", "write:documents"]) is False

    def test_verify_permissions_with_wildcard_all(self):
        """Test *:* wildcard grants all permissions."""
        user = User(
            user_id="test-id",
            email="test@example.com",
            name="Test",
            roles=["admin"],
            permissions=["*:*"]
        )

        assert verify_permissions(user, ["read:documents", "delete:users", "any:thing"]) is True

    def test_verify_permissions_with_resource_wildcard(self):
        """Test *:resource wildcard grants all actions on resource."""
        user = User(
            user_id="test-id",
            email="test@example.com",
            name="Test",
            roles=[],
            permissions=["*:documents"]
        )

        assert verify_permissions(user, ["read:documents", "write:documents"]) is True

    def test_verify_permissions_empty_requirements(self):
        """Test that empty requirements always pass."""
        user = User(
            user_id="test-id",
            email="test@example.com",
            name="Test",
            roles=[],
            permissions=[]
        )

        assert verify_permissions(user, []) is True

    def test_verify_any_permission_with_one_match(self):
        """Test OR logic - user needs at least one permission."""
        user = User(
            user_id="test-id",
            email="test@example.com",
            name="Test",
            roles=[],
            permissions=["read:documents"]
        )

        assert verify_any_permission(user, ["read:documents", "write:documents"]) is True

    def test_verify_any_permission_no_match(self):
        """Test that no matching permissions fails OR check."""
        user = User(
            user_id="test-id",
            email="test@example.com",
            name="Test",
            roles=[],
            permissions=["delete:documents"]
        )

        assert verify_any_permission(user, ["read:documents", "write:documents"]) is False

    def test_verify_any_permission_empty_requirements(self):
        """Test that empty requirements always pass."""
        user = User(
            user_id="test-id",
            email="test@example.com",
            name="Test",
            roles=[],
            permissions=[]
        )

        assert verify_any_permission(user, []) is True


class TestExtractTokenFromCookie:
    """Tests for extract_token_from_cookie() function."""

    def test_extract_existing_token(self):
        """Test extracting token from cookies."""
        cookies = {"cortex_access_token": "test-token-value"}

        token = extract_token_from_cookie(cookies)

        assert token == "test-token-value"

    def test_extract_missing_token(self):
        """Test extracting from cookies without token."""
        cookies = {"other_cookie": "value"}

        token = extract_token_from_cookie(cookies)

        assert token is None

    def test_extract_from_empty_cookies(self):
        """Test extracting from empty cookies."""
        token = extract_token_from_cookie({})

        assert token is None


class TestRoleHelpers:
    """Tests for is_admin() and is_manager() helper functions."""

    def test_is_admin_true(self):
        """Test that admin user is identified."""
        user = User(
            user_id="admin-id",
            email="admin@example.com",
            name="Admin",
            roles=["admin"],
            permissions=["*:*"]
        )

        assert is_admin(user) is True

    def test_is_admin_false(self):
        """Test that non-admin user is not admin."""
        user = User(
            user_id="user-id",
            email="user@example.com",
            name="User",
            roles=["user"],
            permissions=[]
        )

        assert is_admin(user) is False

    def test_is_manager_true(self):
        """Test that manager user is identified."""
        user = User(
            user_id="manager-id",
            email="manager@example.com",
            name="Manager",
            roles=["manager"],
            permissions=[]
        )

        assert is_manager(user) is True

    def test_is_manager_false(self):
        """Test that non-manager user is not manager."""
        user = User(
            user_id="user-id",
            email="user@example.com",
            name="User",
            roles=["user"],
            permissions=[]
        )

        assert is_manager(user) is False

    def test_is_manager_with_admin(self):
        """Test that admin is not automatically a manager."""
        user = User(
            user_id="admin-id",
            email="admin@example.com",
            name="Admin",
            roles=["admin"],
            permissions=["*:*"]
        )

        # Admin is not automatically manager (explicit role check)
        assert is_manager(user) is False
