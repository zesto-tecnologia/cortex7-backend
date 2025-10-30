"""
Test fixtures for Gateway service tests.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from jose import jwt
import secrets

# Import after creating test keys
from services.gateway.main import app
from services.gateway.config import settings as gateway_settings
from cortex_auth import settings as auth_settings


# Generate test RSA keys for testing
TEST_PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDg1ghthNm7EUfw
/Sx1Mw+j5wLm+yJHhDlb7OJaCpEEILqgFrU+wv6luTviD/E+PjWTQCrLik8HCaWj
Pr9awtnRZG8APzaVdGBBMXDw7t+9kxb3XQYh/7Tg1BvobJ/seSmWDele8GZqjc2+
b4MfZGTv/wItyhivVdFf4iqj/U7vbfV3rhnqzrZd0kEMq1jiqBxoilnqM3zTeJqx
IR9zF68mvHaUrsFMROEDhgU24JAj7NbsO/wDJdLSCZD41HemOEsbkn7UgIAeSaTm
pNEveHXbFLOyDVmz27H/rfna+WsMwiGYb6ERtgT/8DknziX+JOXGIUpMZlcVqOhN
lbKDX8h1AgMBAAECggEAD1A58Lj8r2i6PVKxECZzKUGsXpkPjk7A2Ammp7qn19/M
IOfgXlmfncqjpn5ZewN3rgN6fAnRNMnWa0D0fYpfQDYWoq4A2hBmwen2fE0ja2EK
Tmdv6dQ7De5vHCx8fqRd+GdoKVw2+DOXpiHS4h96CdKU474rt5LLw5EUQGkZ/Y/0
rPT+U1mlX0EPUiJDLErSF3t4UO7Pgx2vB1lGaca0F93MO13B2nyOubXb11ki2d3R
Ee+mYXfTvkhgXzBececdLpeH8gHK2LOOGd512XkVgi1u85OYdVGrpOPN1sAOZIqL
IvH72Cl/ATHB9eTUkfYU2VO2dyKCqu3qjju3vfXc/QKBgQD2jJ04DIt5gv67BcDE
/doaSqkZl1TfZyAS4fARNdsRRFbnJVjc00BOTAzGtYR/yInhd4PZhSH9jQHsO9gn
4A+CrMK9Ohu0qx4SNWoO8+dkeaTPr4WZAzxz6z3xL2W/BxZGiUOITFlEHdw0SNv8
YguQ9zWEMYDHouVKmRAVwaIPRwKBgQDpdFjmb8kJYKkz+8aU0Vzee9j3Rb9yglHK
/FkyT4Z+WKmmidBJvgbkrSetWtIGguvN4M43V6w+mYpoGplODpnbZR3M8nGrSQ0E
CJ7uNNJzPwxgrGAZ9B4vAJs8RjkMNJHbAxoyJn87RVRvfTElh9XgjTOg7j10OBkK
6fBsFV0gYwKBgDY4tHbYI3Bkw7rDyCJKpcW0d73+DxdWqbIdaFuQmY4Rln8dMo7W
EsVlakXlM6+aneAtFZ0n71LAyRR4ENCsMR0O+4D8H427OFDO2HVTZKcvLXTTaDE/
ifMAYE4Dm3/IgjifBXAbQmJ9oqkJAQBfW6XVCDr7XBQLmhuuz9/JBugPAoGBALvM
THeTFTXl/DdFIso0YXDYUAEaqpeDHikcNuSx9I9O46qE0nl/1CvA31ok5S83wlkr
rrf2Xyk8eoqkWw7f0AUdootrvOT9Lus/xBn7hBARd/OMtwIpzt4grsAd/WZEI9D6
/ee58D/N1c6Z9x8p1nN9Izsia21Cc2LELhPEW9XhAoGBALuuKYmJWTMGuj5d1Rse
s1fVhTiRUVEUAvOfJY0l4HB6ZnSsQV6+//r7CtLpsQdFKpRQ5N+IsHRrSxHYkwNE
e7vRhAZvUOGxDHCFl3tURDqQI+hrS6cPAzfmB24cb1hyxIOXxNdkp+oMnUKSmtYQ
iyyMFIXkdtGYuZbZTQg72y6/
-----END PRIVATE KEY-----"""

TEST_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA4NYIbYTZuxFH8P0sdTMP
o+cC5vsiR4Q5W+ziWgqRBCC6oBa1PsL+pbk74g/xPj41k0Aqy4pPBwmloz6/WsLZ
0WRvAD82lXRgQTFw8O7fvZMW910GIf+04NQb6Gyf7Hkplg3pXvBmao3Nvm+DH2Rk
7/8CLcoYr1XRX+Iqo/1O7231d64Z6s62XdJBDKtY4qgcaIpZ6jN803iasSEfcxev
Jrx2lK7BTEThA4YFNuCQI+zW7Dv8AyXS0gmQ+NR3pjhLG5J+1ICAHkmk5qTRL3h1
2xSzsg1Zs9ux/6352vlrDMIhmG+hEbYE//A5J84l/iTlxiFKTGZXFajoTZWyg1/I
dQIDAQAB
-----END PUBLIC KEY-----"""


@pytest.fixture
def test_client():
    """Create test client with mocked settings."""
    with patch.object(auth_settings, "auth_public_key", TEST_PUBLIC_KEY):
        with patch.object(gateway_settings, "auth_enabled", True):
            with patch.object(gateway_settings, "canary_enabled", False):  # Disable for deterministic tests
                client = TestClient(app)
                yield client


@pytest.fixture
def admin_token():
    """Generate valid admin JWT token for testing."""
    payload = {
        "user_id": "admin-123",
        "email": "admin@test.com",
        "name": "Admin User",
        "roles": ["admin"],
        "permissions": ["*:*"],
        "iss": "cortex-auth-service",
        "iat": datetime.now(timezone.utc).timestamp(),
        "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp(),
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, TEST_PRIVATE_KEY, algorithm="RS256")


@pytest.fixture
def user_token():
    """Generate valid user JWT token for testing."""
    payload = {
        "user_id": "user-456",
        "email": "user@test.com",
        "name": "Regular User",
        "roles": ["user"],
        "permissions": ["read:own_data", "write:own_posts"],
        "iss": "cortex-auth-service",
        "iat": datetime.now(timezone.utc).timestamp(),
        "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp(),
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, TEST_PRIVATE_KEY, algorithm="RS256")


@pytest.fixture
def expired_token():
    """Generate expired JWT token for testing."""
    payload = {
        "user_id": "user-789",
        "email": "expired@test.com",
        "name": "Expired User",
        "roles": ["user"],
        "permissions": [],
        "iss": "cortex-auth-service",
        "iat": (datetime.now(timezone.utc) - timedelta(hours=2)).timestamp(),
        "exp": (datetime.now(timezone.utc) - timedelta(hours=1)).timestamp(),
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, TEST_PRIVATE_KEY, algorithm="RS256")


@pytest.fixture
def invalid_token():
    """Generate token with invalid signature."""
    payload = {
        "user_id": "user-999",
        "email": "invalid@test.com",
        "name": "Invalid User",
        "roles": ["user"],
        "permissions": [],
        "iss": "cortex-auth-service",
        "iat": datetime.now(timezone.utc).timestamp(),
        "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp(),
    }
    # Sign with wrong key
    wrong_key = "wrong-key-for-testing-invalid-signature"
    return jwt.encode(payload, wrong_key, algorithm="HS256")


@pytest.fixture
def mock_backend_service(monkeypatch):
    """Mock httpx.AsyncClient for backend service calls."""
    async def mock_get(*args, **kwargs):
        response = MagicMock()
        response.status_code = 200
        response.json = lambda: {"status": "ok", "service": "mocked"}
        response.content = b'{"status": "ok"}'
        response.headers = {"content-type": "application/json"}
        return response

    async def mock_post(*args, **kwargs):
        response = MagicMock()
        response.status_code = 201
        response.json = lambda: {"created": True}
        response.content = b'{"created": true}'
        response.headers = {"content-type": "application/json"}
        return response

    mock_client = MagicMock()
    mock_client.get = mock_get
    mock_client.post = mock_post
    mock_client.__aenter__ = MagicMock(return_value=mock_client)
    mock_client.__aexit__ = MagicMock(return_value=None)

    monkeypatch.setattr("httpx.AsyncClient", lambda *args, **kwargs: mock_client)
    return mock_client
