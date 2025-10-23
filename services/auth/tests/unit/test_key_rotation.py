"""Unit tests for Key Rotation Service."""

import pytest
import os
from pathlib import Path
from datetime import datetime, timedelta

from services.auth.services.key_rotation import KeyRotationService
from services.auth.core.cache import RedisClient


@pytest.fixture
async def key_rotation_service(redis_client: RedisClient):
    """Create key rotation service instance."""
    return KeyRotationService()


@pytest.fixture
def temp_key_dir(tmp_path):
    """Create temporary directory for test keys."""
    key_dir = tmp_path / "test_keys"
    key_dir.mkdir()
    return key_dir


class TestKeyGeneration:
    """Test RSA key pair generation."""

    @pytest.mark.asyncio
    async def test_generate_key_pair(self, key_rotation_service: KeyRotationService):
        """Test generating RSA key pair."""
        private_key, public_key = key_rotation_service.generate_key_pair()

        assert isinstance(private_key, bytes)
        assert isinstance(public_key, bytes)
        assert b"BEGIN PRIVATE KEY" in private_key
        assert b"BEGIN PUBLIC KEY" in public_key

    @pytest.mark.asyncio
    async def test_key_pair_size(self, key_rotation_service: KeyRotationService):
        """Test generated keys are 2048 bits."""
        private_key, public_key = key_rotation_service.generate_key_pair()

        # Keys should be non-trivial size for 2048 bits
        assert len(private_key) > 1000
        assert len(public_key) > 200


class TestJWKGeneration:
    """Test JWK Set generation."""

    @pytest.mark.asyncio
    async def test_get_jwks_structure(self, key_rotation_service: KeyRotationService):
        """Test JWK Set has correct structure."""
        jwks = await key_rotation_service.get_jwks()

        assert "keys" in jwks
        assert isinstance(jwks["keys"], list)

    @pytest.mark.asyncio
    async def test_jwk_key_properties(self, key_rotation_service: KeyRotationService):
        """Test individual JWK has required properties."""
        jwks = await key_rotation_service.get_jwks()

        if len(jwks["keys"]) > 0:
            key = jwks["keys"][0]

            # RFC 7517 required properties
            assert key["kty"] == "RSA"
            assert key["use"] == "sig"
            assert key["alg"] == "RS256"
            assert "kid" in key
            assert "n" in key  # RSA modulus
            assert "e" in key  # RSA exponent


class TestRotationStatus:
    """Test rotation status checking."""

    @pytest.mark.asyncio
    async def test_should_rotate_no_metadata(
        self,
        key_rotation_service: KeyRotationService,
        redis_client: RedisClient
    ):
        """Test should rotate when no metadata exists."""
        # Clear any existing metadata
        await redis_client.delete("jwt:key:metadata")

        should_rotate = await key_rotation_service.should_rotate()

        assert should_rotate is True

    @pytest.mark.asyncio
    async def test_get_rotation_status_no_metadata(
        self,
        key_rotation_service: KeyRotationService,
        redis_client: RedisClient
    ):
        """Test rotation status when no metadata exists."""
        await redis_client.delete("jwt:key:metadata")

        status = await key_rotation_service.get_rotation_status()

        assert status["status"] == "unknown"
        assert "message" in status

    @pytest.mark.asyncio
    async def test_get_rotation_status_with_metadata(
        self,
        key_rotation_service: KeyRotationService,
        redis_client: RedisClient
    ):
        """Test rotation status with valid metadata."""
        # Create metadata
        rotated_at = datetime.utcnow()
        next_rotation = rotated_at + timedelta(days=90)

        metadata = {
            "rotated_at": rotated_at.isoformat(),
            "next_rotation": next_rotation.isoformat(),
            "key_size": 2048,
            "algorithm": "RS256"
        }

        await redis_client.set_json(
            "jwt:key:metadata",
            metadata,
            ex=86400 * 97  # 97 days
        )

        status = await key_rotation_service.get_rotation_status()

        assert status["status"] == "active"
        assert status["key_size"] == 2048
        assert status["algorithm"] == "RS256"
        assert "days_until_rotation" in status

    @pytest.mark.asyncio
    async def test_rotation_warning_threshold(
        self,
        key_rotation_service: KeyRotationService,
        redis_client: RedisClient
    ):
        """Test rotation warning when close to rotation date."""
        # Set rotation to 5 days from now (within 7-day warning threshold)
        rotated_at = datetime.utcnow() - timedelta(days=85)
        next_rotation = datetime.utcnow() + timedelta(days=5)

        metadata = {
            "rotated_at": rotated_at.isoformat(),
            "next_rotation": next_rotation.isoformat(),
            "key_size": 2048,
            "algorithm": "RS256"
        }

        await redis_client.set_json("jwt:key:metadata", metadata)

        status = await key_rotation_service.get_rotation_status()

        assert status["should_rotate_soon"] is True
