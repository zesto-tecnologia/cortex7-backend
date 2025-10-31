"""Token schemas for JWT management."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Optional


class RefreshTokenData(BaseModel):
    """Refresh token data schema."""

    id: UUID
    user_id: UUID
    expires_at: datetime
    revoked: bool
    created_at: datetime

    class Config:
        from_attributes = True


class JWKSKey(BaseModel):
    """JSON Web Key Set (JWKS) key schema."""

    kid: str
    kty: str = "RSA"
    use: str = "sig"
    alg: str = "RS256"
    n: str  # RSA modulus
    e: str  # RSA public exponent


class JWKSResponse(BaseModel):
    """JWKS endpoint response schema."""

    keys: list[JWKSKey]