"""Security utilities for password hashing and token generation."""

import secrets
import hashlib
from passlib.context import CryptContext


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def generate_token(length: int = 32) -> str:
    """Generate a random token."""
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    """Hash a token using SHA256 for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_kid() -> str:
    """Generate a unique key ID for JWT signing keys."""
    return secrets.token_urlsafe(16)