"""User schemas for data validation."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    name: str


class UserCreate(UserBase):
    """User creation schema."""

    id: Optional[UUID] = None
    password_hash: Optional[str] = None  # For local auth; None for OAuth
    role: str = "user"
    email_verified: bool = False
    auth_provider: Optional[str] = None


class UserUpdate(BaseModel):
    """User update schema - all fields optional."""

    name: Optional[str] = None
    email: Optional[EmailStr] = None
    last_login: Optional[datetime] = None


class UserInDB(UserBase):
    """User database schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str
    email_verified: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class UserCompanyData(BaseModel):
    """User company association schema."""

    model_config = ConfigDict(from_attributes=True)

    company_id: UUID
    is_primary: bool
    joined_at: datetime


class UserWithCompanies(UserInDB):
    """User with company associations schema."""

    companies: list[UserCompanyData] = []