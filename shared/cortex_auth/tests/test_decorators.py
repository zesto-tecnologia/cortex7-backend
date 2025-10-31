"""
Comprehensive tests for cortex-auth decorators.

Tests all authentication and authorization decorators with various scenarios
including valid tokens, expired tokens, invalid tokens, missing tokens,
role validation, permission validation, and decorator composition.
"""

import pytest
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from jose import jwt

from cortex_auth.decorators import (
    require_auth,
    require_roles,
    require_permissions,
    require_admin,
    require_manager,
)
from cortex_auth.models import User


# Test FastAPI app
app = FastAPI()


@app.get("/protected")
@require_auth
async def protected_route(request: Request):
    """Test endpoint requiring authentication."""
    user = request.state.user
    return {"message": f"Hello {user.name}", "user_id": user.user_id}


@app.get("/admin-only")
@require_admin
async def admin_route(request: Request):
    """Test endpoint requiring admin role."""
    user = request.state.user
    return {"message": "Admin access granted", "user_id": user.user_id}


@app.get("/manager-only")
@require_manager
async def manager_route(request: Request):
    """Test endpoint requiring manager role."""
    user = request.state.user
    return {"message": "Manager access granted", "user_id": user.user_id}


@app.get("/admin-or-manager")
@require_roles(["admin", "manager"])
async def admin_or_manager_route(request: Request):
    """Test endpoint requiring admin OR manager role."""
    user = request.state.user
    return {"message": "Admin or manager access", "user_id": user.user_id}


@app.get("/admin-and-manager")
@require_roles(["admin", "manager"], require_all=True)
async def admin_and_manager_route(request: Request):
    """Test endpoint requiring admin AND manager roles."""
    user = request.state.user
    return {"message": "Admin and manager access", "user_id": user.user_id}


@app.get("/read-documents")
@require_permissions(["read:documents"])
async def read_documents_route(request: Request):
    """Test endpoint requiring read:documents permission."""
    user = request.state.user
    return {"message": "Reading documents", "user_id": user.user_id}


@app.get("/write-documents")
@require_permissions(["write:documents"])
async def write_documents_route(request: Request):
    """Test endpoint requiring write:documents permission."""
    user = request.state.user
    return {"message": "Writing documents", "user_id": user.user_id}


@app.get("/read-and-write-documents")
@require_permissions(["read:documents", "write:documents"], require_all=True)
async def read_and_write_documents_route(request: Request):
    """Test endpoint requiring both read and write permissions."""
    user = request.state.user
    return {"message": "Reading and writing documents", "user_id": user.user_id}


@app.get("/read-or-write-documents")
@require_permissions(["read:documents", "write:documents"], require_all=False)
async def read_or_write_documents_route(request: Request):
    """Test endpoint requiring read OR write permission."""
    user = request.state.user
    return {"message": "Read or write access", "user_id": user.user_id}


@app.get("/wildcard-reports")
@require_permissions(["*:reports"])
async def wildcard_reports_route(request: Request):
    """Test endpoint with wildcard permission."""
    user = request.state.user
    return {"message": "Access to reports", "user_id": user.user_id}


class TestRequireAuthDecorator:
    """Tests for @require_auth decorator."""

    def test_valid_token(self, mock_settings, create_jwt_token, valid_token_payload):
        """Test that valid token grants access."""
        token = create_jwt_token(valid_token_payload)
        client = TestClient(app)

        response = client.get(
            "/protected",
            cookies={"cortex_access_token": token}
        )

        # Debug: Print response if test fails
        if response.status_code != 200:
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")

        assert response.status_code == 200
        assert response.json()["message"] == "Hello Test User"
        assert response.json()["user_id"] == valid_token_payload["user_id"]

    def test_missing_token(self, mock_settings):
        """Test that missing token returns 401."""
        client = TestClient(app)

        response = client.get("/protected")

        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "token_missing"
        assert "Authentication required" in response.json()["detail"]["message"]

    def test_expired_token(self, mock_settings, create_jwt_token, valid_token_payload):
        """Test that expired token returns 401 with token_expired code."""
        expired_token = create_jwt_token(valid_token_payload, expired=True)
        client = TestClient(app)

        response = client.get(
            "/protected",
            cookies={"cortex_access_token": expired_token}
        )

        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "token_expired"

    def test_invalid_signature(self, mock_settings, rsa_keys, valid_token_payload):
        """Test that token with invalid signature returns 401."""
        # Create a different key pair
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization

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

        client = TestClient(app)
        response = client.get(
            "/protected",
            cookies={"cortex_access_token": invalid_token}
        )

        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "token_invalid"

    def test_invalid_issuer(self, mock_settings, create_jwt_token, valid_token_payload):
        """Test that token with wrong issuer returns 401."""
        invalid_token = create_jwt_token(valid_token_payload, wrong_issuer=True)
        client = TestClient(app)

        response = client.get(
            "/protected",
            cookies={"cortex_access_token": invalid_token}
        )

        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "issuer_invalid"

    def test_malformed_token(self, mock_settings):
        """Test that malformed token returns 401."""
        client = TestClient(app)

        response = client.get(
            "/protected",
            cookies={"cortex_access_token": "not-a-valid-jwt"}
        )

        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "token_invalid"


class TestRequireRolesDecorator:
    """Tests for @require_roles decorator."""

    def test_admin_route_with_admin_role(self, mock_settings, create_jwt_token):
        """Test that admin can access admin-only route."""
        payload = {
            "user_id": "admin-id",
            "email": "admin@example.com",
            "name": "Admin",
            "roles": ["admin"],
            "permissions": ["*:*"],
            "iss": "cortex-auth-service",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "jti": "test-jwt-id"
        }
        token = create_jwt_token(payload)
        client = TestClient(app)

        response = client.get(
            "/admin-only",
            cookies={"cortex_access_token": token}
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Admin access granted"

    def test_admin_route_with_non_admin(self, mock_settings, create_jwt_token):
        """Test that non-admin cannot access admin-only route."""
        payload = {
            "user_id": "user-id",
            "email": "user@example.com",
            "name": "User",
            "roles": ["user"],
            "permissions": ["read:documents"],
            "iss": "cortex-auth-service",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "jti": "test-jwt-id"
        }
        token = create_jwt_token(payload)
        client = TestClient(app)

        response = client.get(
            "/admin-only",
            cookies={"cortex_access_token": token}
        )

        # Debug output
        if response.status_code != 403:
            print(f"Expected 403, got {response.status_code}")
            print(f"Response: {response.json()}")

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "insufficient_permissions"

    def test_manager_route_with_manager_role(self, mock_settings, create_jwt_token):
        """Test that manager can access manager route."""
        payload = {
            "user_id": "manager-id",
            "email": "manager@example.com",
            "name": "Manager",
            "roles": ["manager"],
            "permissions": ["read:users", "write:posts"],
            "iss": "cortex-auth-service",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "jti": "test-jwt-id"
        }
        token = create_jwt_token(payload)
        client = TestClient(app)

        response = client.get(
            "/manager-only",
            cookies={"cortex_access_token": token}
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Manager access granted"

    def test_admin_or_manager_with_admin(self, mock_settings, create_jwt_token):
        """Test OR logic: admin can access admin-or-manager route."""
        payload = {
            "user_id": "admin-id",
            "email": "admin@example.com",
            "name": "Admin",
            "roles": ["admin"],
            "permissions": ["*:*"],
            "iss": "cortex-auth-service",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "jti": "test-jwt-id"
        }
        token = create_jwt_token(payload)
        client = TestClient(app)

        response = client.get(
            "/admin-or-manager",
            cookies={"cortex_access_token": token}
        )

        assert response.status_code == 200

    def test_admin_or_manager_with_manager(self, mock_settings, create_jwt_token):
        """Test OR logic: manager can access admin-or-manager route."""
        payload = {
            "user_id": "manager-id",
            "email": "manager@example.com",
            "name": "Manager",
            "roles": ["manager"],
            "permissions": ["read:users"],
            "iss": "cortex-auth-service",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "jti": "test-jwt-id"
        }
        token = create_jwt_token(payload)
        client = TestClient(app)

        response = client.get(
            "/admin-or-manager",
            cookies={"cortex_access_token": token}
        )

        assert response.status_code == 200

    def test_admin_or_manager_with_user(self, mock_settings, create_jwt_token):
        """Test OR logic: regular user cannot access admin-or-manager route."""
        payload = {
            "user_id": "user-id",
            "email": "user@example.com",
            "name": "User",
            "roles": ["user"],
            "permissions": ["read:documents"],
            "iss": "cortex-auth-service",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "jti": "test-jwt-id"
        }
        token = create_jwt_token(payload)
        client = TestClient(app)

        response = client.get(
            "/admin-or-manager",
            cookies={"cortex_access_token": token}
        )

        assert response.status_code == 403

    def test_admin_and_manager_with_both_roles(self, mock_settings, create_jwt_token):
        """Test AND logic: user with both roles can access."""
        payload = {
            "user_id": "super-user-id",
            "email": "super@example.com",
            "name": "Super User",
            "roles": ["admin", "manager"],
            "permissions": ["*:*"],
            "iss": "cortex-auth-service",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "jti": "test-jwt-id"
        }
        token = create_jwt_token(payload)
        client = TestClient(app)

        response = client.get(
            "/admin-and-manager",
            cookies={"cortex_access_token": token}
        )

        assert response.status_code == 200

    def test_admin_and_manager_with_only_admin(self, mock_settings, create_jwt_token):
        """Test AND logic: user with only admin role cannot access."""
        payload = {
            "user_id": "admin-id",
            "email": "admin@example.com",
            "name": "Admin",
            "roles": ["admin"],
            "permissions": ["*:*"],
            "iss": "cortex-auth-service",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "jti": "test-jwt-id"
        }
        token = create_jwt_token(payload)
        client = TestClient(app)

        response = client.get(
            "/admin-and-manager",
            cookies={"cortex_access_token": token}
        )

        assert response.status_code == 403


class TestRequirePermissionsDecorator:
    """Tests for @require_permissions decorator."""

    def test_read_permission_granted(self, mock_settings, create_jwt_token):
        """Test that user with read:documents can access read endpoint."""
        payload = {
            "user_id": "user-id",
            "email": "user@example.com",
            "name": "User",
            "roles": ["user"],
            "permissions": ["read:documents"],
            "iss": "cortex-auth-service",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "jti": "test-jwt-id"
        }
        token = create_jwt_token(payload)
        client = TestClient(app)

        response = client.get(
            "/read-documents",
            cookies={"cortex_access_token": token}
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Reading documents"

    def test_read_permission_denied(self, mock_settings, create_jwt_token):
        """Test that user without read:documents cannot access read endpoint."""
        payload = {
            "user_id": "user-id",
            "email": "user@example.com",
            "name": "User",
            "roles": ["user"],
            "permissions": ["write:documents"],  # Only write, no read
            "iss": "cortex-auth-service",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "jti": "test-jwt-id"
        }
        token = create_jwt_token(payload)
        client = TestClient(app)

        response = client.get(
            "/read-documents",
            cookies={"cortex_access_token": token}
        )

        assert response.status_code == 403

    def test_both_permissions_required_success(self, mock_settings, create_jwt_token):
        """Test AND logic: user with both permissions can access."""
        payload = {
            "user_id": "user-id",
            "email": "user@example.com",
            "name": "User",
            "roles": ["user"],
            "permissions": ["read:documents", "write:documents"],
            "iss": "cortex-auth-service",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "jti": "test-jwt-id"
        }
        token = create_jwt_token(payload)
        client = TestClient(app)

        response = client.get(
            "/read-and-write-documents",
            cookies={"cortex_access_token": token}
        )

        assert response.status_code == 200

    def test_both_permissions_required_failure(self, mock_settings, create_jwt_token):
        """Test AND logic: user with only one permission cannot access."""
        payload = {
            "user_id": "user-id",
            "email": "user@example.com",
            "name": "User",
            "roles": ["user"],
            "permissions": ["read:documents"],  # Missing write permission
            "iss": "cortex-auth-service",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "jti": "test-jwt-id"
        }
        token = create_jwt_token(payload)
        client = TestClient(app)

        response = client.get(
            "/read-and-write-documents",
            cookies={"cortex_access_token": token}
        )

        assert response.status_code == 403

    def test_any_permission_success_with_read(self, mock_settings, create_jwt_token):
        """Test OR logic: user with read permission can access."""
        payload = {
            "user_id": "user-id",
            "email": "user@example.com",
            "name": "User",
            "roles": ["user"],
            "permissions": ["read:documents"],  # Only read
            "iss": "cortex-auth-service",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "jti": "test-jwt-id"
        }
        token = create_jwt_token(payload)
        client = TestClient(app)

        response = client.get(
            "/read-or-write-documents",
            cookies={"cortex_access_token": token}
        )

        assert response.status_code == 200

    def test_any_permission_success_with_write(self, mock_settings, create_jwt_token):
        """Test OR logic: user with write permission can access."""
        payload = {
            "user_id": "user-id",
            "email": "user@example.com",
            "name": "User",
            "roles": ["user"],
            "permissions": ["write:documents"],  # Only write
            "iss": "cortex-auth-service",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "jti": "test-jwt-id"
        }
        token = create_jwt_token(payload)
        client = TestClient(app)

        response = client.get(
            "/read-or-write-documents",
            cookies={"cortex_access_token": token}
        )

        assert response.status_code == 200

    def test_any_permission_failure(self, mock_settings, create_jwt_token):
        """Test OR logic: user with neither permission cannot access."""
        payload = {
            "user_id": "user-id",
            "email": "user@example.com",
            "name": "User",
            "roles": ["user"],
            "permissions": ["delete:documents"],  # Neither read nor write
            "iss": "cortex-auth-service",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "jti": "test-jwt-id"
        }
        token = create_jwt_token(payload)
        client = TestClient(app)

        response = client.get(
            "/read-or-write-documents",
            cookies={"cortex_access_token": token}
        )

        assert response.status_code == 403

    def test_wildcard_resource_permission(self, mock_settings, create_jwt_token):
        """Test that wildcard *:reports grants access to wildcard endpoint."""
        payload = {
            "user_id": "user-id",
            "email": "user@example.com",
            "name": "User",
            "roles": ["user"],
            "permissions": ["*:reports"],  # Wildcard action on reports
            "iss": "cortex-auth-service",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "jti": "test-jwt-id"
        }
        token = create_jwt_token(payload)
        client = TestClient(app)

        response = client.get(
            "/wildcard-reports",
            cookies={"cortex_access_token": token}
        )

        assert response.status_code == 200

    def test_wildcard_all_permissions(self, mock_settings, create_jwt_token):
        """Test that *:* wildcard grants access to any endpoint."""
        payload = {
            "user_id": "admin-id",
            "email": "admin@example.com",
            "name": "Admin",
            "roles": ["admin"],
            "permissions": ["*:*"],  # All permissions
            "iss": "cortex-auth-service",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "jti": "test-jwt-id"
        }
        token = create_jwt_token(payload)
        client = TestClient(app)

        # Should be able to access any permission-protected endpoint
        response1 = client.get(
            "/read-documents",
            cookies={"cortex_access_token": token}
        )
        assert response1.status_code == 200

        response2 = client.get(
            "/write-documents",
            cookies={"cortex_access_token": token}
        )
        assert response2.status_code == 200

        response3 = client.get(
            "/wildcard-reports",
            cookies={"cortex_access_token": token}
        )
        assert response3.status_code == 200


class TestDecoratorComposition:
    """Tests for combining multiple decorators."""

    def test_auth_and_role_composition(self, mock_settings, create_jwt_token):
        """Test that decorators compose correctly (auth + role check)."""
        payload = {
            "user_id": "admin-id",
            "email": "admin@example.com",
            "name": "Admin",
            "roles": ["admin"],
            "permissions": ["*:*"],
            "iss": "cortex-auth-service",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "jti": "test-jwt-id"
        }
        token = create_jwt_token(payload)
        client = TestClient(app)

        # Should pass both auth and admin role check
        response = client.get(
            "/admin-only",
            cookies={"cortex_access_token": token}
        )

        assert response.status_code == 200

    def test_missing_token_with_role_decorator(self, mock_settings):
        """Test that role decorator returns 401 for missing token (not 403)."""
        client = TestClient(app)

        # Should fail at auth level (401) before checking role
        response = client.get("/admin-only")

        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "token_missing"

    def test_expired_token_with_role_decorator(self, mock_settings, create_jwt_token):
        """Test that role decorator returns 401 for expired token."""
        payload = {
            "user_id": "admin-id",
            "email": "admin@example.com",
            "name": "Admin",
            "roles": ["admin"],
            "permissions": ["*:*"],
            "iss": "cortex-auth-service",
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "jti": "test-jwt-id"
        }
        expired_token = create_jwt_token(payload, expired=True)
        client = TestClient(app)

        # Should fail at auth level (401) before checking role
        response = client.get(
            "/admin-only",
            cookies={"cortex_access_token": expired_token}
        )

        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "token_expired"


class TestRequestStateCaching:
    """Tests for request.state.user caching."""

    def test_user_attached_to_request_state(self, mock_settings, create_jwt_token):
        """Test that user is attached to request.state after authentication."""
        payload = {
            "user_id": "user-id",
            "email": "user@example.com",
            "name": "Test User",
            "roles": ["user"],
            "permissions": ["read:documents"],
            "iss": "cortex-auth-service",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "jti": "test-jwt-id"
        }
        token = create_jwt_token(payload)
        client = TestClient(app)

        response = client.get(
            "/protected",
            cookies={"cortex_access_token": token}
        )

        assert response.status_code == 200
        # Verify user data is correctly extracted from token
        assert response.json()["user_id"] == "user-id"
        assert response.json()["message"] == "Hello Test User"
