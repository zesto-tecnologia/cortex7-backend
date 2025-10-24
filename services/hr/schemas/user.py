"""
Pydantic schemas for Usuários (Users).
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    """Base schema for User."""

    company_id: UUID
    department_id: Optional[UUID] = None
    name: str = Field(..., max_length=255)
    email: EmailStr
    position: Optional[str] = Field(None, max_length=100)
    benefits: Optional[Dict[str, float]] = None
    status: str = Field(default="active", max_length=20)


class UserCreate(UserBase):
    """Schema for creating a User."""
    pass


class UserUpdate(BaseModel):
    """Schema for updating a User."""

    department_id: Optional[UUID] = None
    name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    position: Optional[str] = Field(None, max_length=100)
    benefits: Optional[Dict[str, float]] = None
    status: Optional[str] = Field(None, max_length=20)


class UserResponse(UserBase):
    """Schema for User response."""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True