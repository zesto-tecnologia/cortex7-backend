"""Authentication schemas for request/response validation."""

from datetime import datetime, timezone
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, Any


class UserRegisterRequest(BaseModel):
    """User registration request schema."""

    invite_code: str = Field(min_length=1, max_length=64, description="Invite code required for registration")
    email: EmailStr
    name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8)

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Enforce password strength requirements."""
        import string

        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in string.punctuation for c in v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserLoginRequest(BaseModel):
    """User login request schema."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(default=600)  # 10 minutes in seconds


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str


class JWTClaims(BaseModel):
    """JWT token claims structure."""

    sub: UUID  # user_id
    email: EmailStr
    name: str
    role: str
    company_id: Optional[UUID] = None
    permissions: list[str] = Field(default_factory=list)
    iat: int
    exp: int
    iss: str = "auth-service"
    aud: str = "cortex-7"


class UserProfile(BaseModel):
    """User profile response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    name: str
    role: str
    email_verified: bool
    created_at: datetime
    updated_at: datetime


class UserProfileUpdate(BaseModel):
    """User profile update request schema."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None


class PasswordChangeRequest(BaseModel):
    """Password change request schema."""

    current_password: str
    new_password: str = Field(min_length=8)

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Enforce password strength requirements."""
        import string

        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        if not any(c in string.punctuation for c in v):
            raise ValueError('Password must contain special character')
        return v


class ForgotPasswordRequest(BaseModel):
    """Forgot password request schema."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request schema."""

    token: str
    new_password: str = Field(min_length=8)

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Enforce password strength requirements."""
        import string

        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        if not any(c in string.punctuation for c in v):
            raise ValueError('Password must contain special character')
        return v


class VerifyEmailRequest(BaseModel):
    """Email verification request schema."""

    token: str


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = "healthy"
    version: str = "1.0.0"


class ReadinessResponse(BaseModel):
    """Readiness check response schema."""

    status: str
    dependencies: dict[str, str]  # service_name -> status


class ErrorResponse(BaseModel):
    """Error response schema."""

    detail: str
    status_code: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserRegisterResponse(BaseModel):
    """User registration response schema."""

    user_id: str
    email: EmailStr
    message: str


class LoginResponse(BaseModel):
    """Login response schema."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int  # seconds
    user: dict[str, Any]


class MessageResponse(BaseModel):
    """Generic message response schema."""

    message: str


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""

    token: str
    new_password: str = Field(min_length=8)

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Enforce password strength requirements."""
        import string

        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        if not any(c in string.punctuation for c in v):
            raise ValueError('Password must contain special character')
        return v


class DeleteUserRequest(BaseModel):
    """Delete user request schema."""

    email: EmailStr


class DeleteUserResponse(BaseModel):
    """Delete user response schema."""

    success: bool
    email: EmailStr
    message: str
