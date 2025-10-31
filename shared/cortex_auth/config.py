"""
Configuration module for cortex-auth library.

This module provides settings management for auth library integration,
including RSA public key loading for JWT validation.
"""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    """
    Authentication settings for cortex-auth library.

    Services using this library must provide:
    - AUTH_PUBLIC_KEY_PATH: Path to RS256 public key file
    OR
    - AUTH_PUBLIC_KEY: Direct public key string

    The public key is used to validate JWT tokens signed by the auth service.
    """

    # Public key configuration (one must be provided)
    auth_public_key_path: Optional[str] = None
    auth_public_key: Optional[str] = None

    # Token issuer validation
    auth_issuer: str = "cortex-auth-service"

    # Clock skew tolerance for token expiration (seconds)
    auth_clock_skew_seconds: int = 60

    # Cookie name for access token
    auth_cookie_name: str = "cortex_access_token"

    # Enable/disable authentication (useful for testing)
    auth_enabled: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_public_key(self) -> str:
        """
        Get RSA public key for JWT validation.

        Priority:
        1. AUTH_PUBLIC_KEY environment variable (direct key string)
        2. AUTH_PUBLIC_KEY_PATH environment variable (path to key file)
        3. Default path: keys/jwt-public.pem

        Returns:
            RSA public key in PEM format

        Raises:
            ValueError: If public key cannot be loaded
        """
        # Direct key provided
        if self.auth_public_key:
            return self.auth_public_key

        # Load from file path
        key_path = self._resolve_key_path()
        if not key_path.exists():
            raise ValueError(
                f"Public key file not found at {key_path}. "
                "Set AUTH_PUBLIC_KEY_PATH or AUTH_PUBLIC_KEY environment variable."
            )

        try:
            return key_path.read_text().strip()
        except Exception as e:
            raise ValueError(f"Failed to read public key from {key_path}: {e}")

    def _resolve_key_path(self) -> Path:
        """
        Resolve public key file path.

        Returns:
            Absolute path to public key file
        """
        if self.auth_public_key_path:
            path = Path(self.auth_public_key_path)
            # If relative path, resolve from project root
            if not path.is_absolute():
                # Try to find project root (contains pyproject.toml)
                current = Path.cwd()
                while current != current.parent:
                    if (current / "pyproject.toml").exists():
                        return current / path
                    current = current.parent
                # Fallback to current directory
                return Path.cwd() / path
            return path

        # Default path: keys/jwt-public.pem from project root
        current = Path.cwd()
        while current != current.parent:
            if (current / "pyproject.toml").exists():
                return current / "keys" / "jwt-public.pem"
            current = current.parent

        # Fallback to current directory
        return Path.cwd() / "keys" / "jwt-public.pem"


# Global settings instance
# Services can override by creating their own instance:
# settings = AuthSettings(auth_public_key_path="/custom/path")
settings = AuthSettings()
