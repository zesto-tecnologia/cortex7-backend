"""Secrets management for production environments."""
import os
import logging
from typing import Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


class SecretsManager:
    """Manage secrets from AWS Secrets Manager or local files."""

    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.client = None

        if environment == "production":
            try:
                import boto3
                self.client = boto3.client(
                    'secretsmanager',
                    region_name=os.getenv('AWS_REGION', 'us-east-1')
                )
            except ImportError:
                logger.warning(
                    "boto3 not installed. AWS Secrets Manager will not be available. "
                    "Install with: pip install boto3"
                )

    @lru_cache(maxsize=10)
    def get_secret(self, secret_name: str, default_path: Optional[str] = None) -> str:
        """
        Get secret from AWS Secrets Manager or local file.

        Args:
            secret_name: Name of the secret in AWS Secrets Manager
            default_path: Path to local file for development

        Returns:
            Secret value as string
        """
        if self.environment == "production" and self.client:
            return self._get_from_aws(secret_name)
        elif default_path and os.path.exists(default_path):
            return self._get_from_file(default_path)
        else:
            raise ValueError(f"Secret not found: {secret_name}")

    def _get_from_aws(self, secret_name: str) -> str:
        """Retrieve secret from AWS Secrets Manager."""
        try:
            logger.info(f"Fetching secret from AWS Secrets Manager: {secret_name}")
            response = self.client.get_secret_value(SecretId=secret_name)

            if 'SecretString' in response:
                return response['SecretString']
            else:
                # Binary secret (not typical for keys, but supported)
                import base64
                return base64.b64decode(response['SecretBinary']).decode('utf-8')

        except Exception as e:
            logger.error(f"Failed to fetch secret from AWS: {e}")
            raise

    def _get_from_file(self, file_path: str) -> str:
        """Read secret from local file."""
        logger.info(f"Reading secret from file: {file_path}")
        with open(file_path, 'r') as f:
            return f.read()

    def get_private_key(self) -> str:
        """Get JWT signing private key."""
        return self.get_secret(
            secret_name="cortex/auth/private-key",
            default_path=os.getenv("AUTH_PRIVATE_KEY_PATH", "./keys/private.pem")
        )

    def get_public_key(self) -> str:
        """Get JWT validation public key."""
        return self.get_secret(
            secret_name="cortex/auth/public-key",
            default_path=os.getenv("AUTH_PUBLIC_KEY_PATH", "./keys/public.pem")
        )

    def rotate_keys(self, new_private_key: str, new_public_key: str) -> None:
        """
        Rotate keys in AWS Secrets Manager.

        This should be done during key rotation procedures.
        """
        if self.environment != "production":
            raise ValueError("Key rotation only supported in production")

        try:
            # Update private key
            self.client.update_secret(
                SecretId="cortex/auth/private-key",
                SecretString=new_private_key
            )

            # Update public key
            self.client.update_secret(
                SecretId="cortex/auth/public-key",
                SecretString=new_public_key
            )

            # Clear cache to force re-fetch
            self.get_secret.cache_clear()

            logger.info("Keys rotated successfully in AWS Secrets Manager")

        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            raise


# Singleton instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager(environment: str = None) -> SecretsManager:
    """Get or create SecretsManager singleton."""
    global _secrets_manager

    if _secrets_manager is None:
        env = environment or os.getenv("ENVIRONMENT", "development")
        _secrets_manager = SecretsManager(environment=env)

    return _secrets_manager
