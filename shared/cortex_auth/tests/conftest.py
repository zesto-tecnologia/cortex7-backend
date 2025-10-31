"""
Pytest configuration and fixtures for cortex-auth tests.
"""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt


@pytest.fixture(scope="session")
def rsa_keys():
    """Generate RSA key pair for testing."""
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # Get private key in PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()

    # Get public key in PEM format
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()

    return {
        "private_key": private_pem,
        "public_key": public_pem
    }


@pytest.fixture
def valid_token_payload():
    """Return a valid token payload dictionary."""
    return {
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "email": "test@example.com",
        "name": "Test User",
        "roles": ["user", "manager"],
        "permissions": ["read:documents", "write:documents", "*:reports"],
        "iss": "cortex-auth-service",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "jti": "test-jwt-id"
    }


@pytest.fixture
def create_jwt_token(rsa_keys):
    """Factory fixture to create JWT tokens."""
    def _create_token(payload: dict, expired: bool = False, wrong_issuer: bool = False):
        token_payload = payload.copy()

        # Convert datetime objects to timestamps for jose
        if isinstance(token_payload.get("iat"), datetime):
            token_payload["iat"] = token_payload["iat"].timestamp()
        if isinstance(token_payload.get("exp"), datetime):
            token_payload["exp"] = token_payload["exp"].timestamp()

        # Modify for expired token
        if expired:
            now = datetime.now(timezone.utc)
            token_payload["exp"] = (now - timedelta(hours=1)).timestamp()
            token_payload["iat"] = (now - timedelta(hours=2)).timestamp()

        # Modify for wrong issuer
        if wrong_issuer:
            token_payload["iss"] = "wrong-issuer"

        # Encode token with private key
        return jwt.encode(
            token_payload,
            rsa_keys["private_key"],
            algorithm="RS256"
        )

    return _create_token


@pytest.fixture
def mock_user():
    """Return a mock User instance for testing."""
    from cortex_auth.models import User

    return User(
        user_id="123e4567-e89b-12d3-a456-426614174000",
        email="test@example.com",
        name="Test User",
        roles=["user", "manager"],
        permissions=["read:documents", "write:documents", "*:reports"]
    )


@pytest.fixture
def admin_user():
    """Return a mock admin User instance for testing."""
    from cortex_auth.models import User

    return User(
        user_id="admin-user-id",
        email="admin@example.com",
        name="Admin User",
        roles=["admin", "manager", "user"],
        permissions=["*:*"]
    )


@pytest.fixture
def basic_user():
    """Return a mock basic User instance for testing."""
    from cortex_auth.models import User

    return User(
        user_id="basic-user-id",
        email="basic@example.com",
        name="Basic User",
        roles=["user"],
        permissions=["read:documents"]
    )


@pytest.fixture
def temp_public_key_file(rsa_keys, tmp_path):
    """Create a temporary public key file."""
    key_file = tmp_path / "jwt-public.pem"
    key_file.write_text(rsa_keys["public_key"])
    return str(key_file)


@pytest.fixture(autouse=True)
def mock_settings(rsa_keys, monkeypatch):
    """Mock auth settings with test RSA keys."""
    # Set environment variables first
    monkeypatch.setenv("AUTH_PUBLIC_KEY", rsa_keys["public_key"])
    monkeypatch.setenv("AUTH_ISSUER", "cortex-auth-service")
    monkeypatch.setenv("AUTH_COOKIE_NAME", "cortex_access_token")
    monkeypatch.setenv("AUTH_ENABLED", "true")

    # Import and patch the global settings instance
    from cortex_auth import config, utils, decorators

    # Create new settings with environment variables
    test_settings = config.AuthSettings(
        auth_public_key=rsa_keys["public_key"],
        auth_issuer="cortex-auth-service",
        auth_cookie_name="cortex_access_token",
        auth_enabled=True
    )

    # Patch the global settings instance in all modules
    monkeypatch.setattr(config, "settings", test_settings)
    monkeypatch.setattr(utils, "settings", test_settings)
    monkeypatch.setattr(decorators, "settings", test_settings)

    return test_settings
