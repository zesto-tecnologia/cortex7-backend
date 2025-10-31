"""JWT Key Rotation Service for automated RSA key management.

This service implements:
- Automated RSA key pair generation
- 90-day rotation cycle with 7-day overlap
- Zero-downtime key rotation
- JWK (JSON Web Key) endpoint for Kong Gateway
"""

from typing import Any
from datetime import datetime, timedelta
import os
import json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import jwt
import structlog

from services.auth.config import settings
from services.auth.core.cache import redis_client

logger = structlog.get_logger(__name__)


class KeyRotationService:
    """Manage RSA key rotation for JWT signing."""

    def __init__(self):
        """Initialize key rotation service."""
        self.key_size = 2048
        self.rotation_days = settings.JWT_KEY_ROTATION_DAYS
        self.overlap_days = 7  # Grace period for old keys

    def generate_key_pair(self) -> tuple[bytes, bytes]:
        """
        Generate new RSA 2048-bit key pair.

        Returns:
            Tuple of (private_pem, public_pem)
        """
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=self.key_size,
            backend=default_backend()
        )

        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(
                settings.JWT_KEY_PASSWORD.encode()
            ) if settings.JWT_KEY_PASSWORD else serialization.NoEncryption()
        )

        # Serialize public key
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return private_pem, public_pem

    async def rotate_keys(self) -> bool:
        """
        Rotate JWT signing keys with zero downtime.

        Process:
        1. Generate new key pair
        2. Backup current keys with timestamp
        3. Write new keys to configured paths
        4. Update metadata in Redis
        5. Old keys remain valid for overlap period

        Returns:
            True if rotation successful, False otherwise
        """
        try:
            logger.info("Starting JWT key rotation")

            # Generate new key pair
            private_key, public_key = self.generate_key_pair()

            # Create backup directory with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path("keys/backups") / timestamp
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Backup current keys if they exist
            if os.path.exists(settings.JWT_PRIVATE_KEY_PATH):
                os.rename(
                    settings.JWT_PRIVATE_KEY_PATH,
                    backup_dir / "private_key.pem"
                )
                logger.info("Current private key backed up", backup_dir=str(backup_dir))

            if os.path.exists(settings.JWT_PUBLIC_KEY_PATH):
                os.rename(
                    settings.JWT_PUBLIC_KEY_PATH,
                    backup_dir / "public_key.pem"
                )
                logger.info("Current public key backed up", backup_dir=str(backup_dir))

            # Write new keys
            with open(settings.JWT_PRIVATE_KEY_PATH, 'wb') as f:
                f.write(private_key)
            with open(settings.JWT_PUBLIC_KEY_PATH, 'wb') as f:
                f.write(public_key)

            # Set appropriate permissions (read-only for private key)
            os.chmod(settings.JWT_PRIVATE_KEY_PATH, 0o600)
            os.chmod(settings.JWT_PUBLIC_KEY_PATH, 0o644)

            # Store key metadata in Redis
            metadata = {
                "rotated_at": datetime.utcnow().isoformat(),
                "next_rotation": (
                    datetime.utcnow() + timedelta(days=self.rotation_days)
                ).isoformat(),
                "backup_location": str(backup_dir),
                "key_size": self.key_size,
                "algorithm": settings.JWT_ALGORITHM
            }

            await redis_client.set_json(
                "jwt:key:metadata",
                metadata,
                ex=86400 * (self.rotation_days + self.overlap_days)
            )

            logger.info(
                "JWT keys rotated successfully",
                backup=str(backup_dir),
                next_rotation=metadata["next_rotation"]
            )

            return True

        except Exception as e:
            logger.error("Key rotation failed", error=str(e))
            return False

    async def get_jwks(self) -> dict[str, Any]:
        """
        Get public keys in JWK Set format for Kong Gateway.

        Returns JWK Set with current and previous public keys for
        zero-downtime rotation.

        Returns:
            JWK Set with format:
            {
                "keys": [
                    {
                        "kty": "RSA",
                        "use": "sig",
                        "kid": "current",
                        "n": "...",
                        "e": "..."
                    }
                ]
            }
        """
        keys = []

        try:
            # Load current public key
            with open(settings.JWT_PUBLIC_KEY_PATH, 'rb') as f:
                public_key = serialization.load_pem_public_key(
                    f.read(),
                    backend=default_backend()
                )

                # Convert to JWK format
                from jwt.algorithms import RSAAlgorithm
                jwk = RSAAlgorithm.to_jwk(public_key)
                jwk_dict = json.loads(jwk)
                jwk_dict["use"] = "sig"
                jwk_dict["kid"] = "current"
                jwk_dict["alg"] = settings.JWT_ALGORITHM
                keys.append(jwk_dict)

            # TODO: Add previous key for overlap period
            # During rotation overlap, both keys should be in the JWK set

            logger.info("JWK set generated", key_count=len(keys))

        except Exception as e:
            logger.error("Failed to generate JWK set", error=str(e))

        return {"keys": keys}

    async def should_rotate(self) -> bool:
        """
        Check if keys should be rotated based on age.

        Returns:
            True if rotation is due, False otherwise
        """
        try:
            metadata = await redis_client.get_json("jwt:key:metadata")
            if not metadata:
                # No metadata means keys were manually created, rotate now
                return True

            next_rotation = datetime.fromisoformat(metadata["next_rotation"])
            return datetime.utcnow() >= next_rotation

        except Exception as e:
            logger.warning("Failed to check rotation status", error=str(e))
            return False

    async def get_rotation_status(self) -> dict[str, Any]:
        """
        Get current key rotation status and metadata.

        Returns:
            Rotation status information
        """
        try:
            metadata = await redis_client.get_json("jwt:key:metadata")
            if not metadata:
                return {
                    "status": "unknown",
                    "message": "No rotation metadata found"
                }

            rotated_at = datetime.fromisoformat(metadata["rotated_at"])
            next_rotation = datetime.fromisoformat(metadata["next_rotation"])
            days_until_rotation = (next_rotation - datetime.utcnow()).days

            return {
                "status": "active",
                "last_rotation": metadata["rotated_at"],
                "next_rotation": metadata["next_rotation"],
                "days_until_rotation": days_until_rotation,
                "key_size": metadata.get("key_size", 2048),
                "algorithm": metadata.get("algorithm", "RS256"),
                "backup_location": metadata.get("backup_location"),
                "should_rotate_soon": days_until_rotation <= 7
            }

        except Exception as e:
            logger.error("Failed to get rotation status", error=str(e))
            return {"status": "error", "error": str(e)}
