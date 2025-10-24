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
    departamento_id: Optional[UUID] = None
    nome: str = Field(..., max_length=255)
    email: EmailStr
    cargo: Optional[str] = Field(None, max_length=100)
    alcadas: Optional[Dict[str, float]] = None
    status: str = Field(default="ativo", max_length=20)


class UserCreate(UserBase):
    """Schema for creating a User."""
    pass


class UserUpdate(BaseModel):
    """Schema for updating a User."""

    departamento_id: Optional[UUID] = None
    nome: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    cargo: Optional[str] = Field(None, max_length=100)
    alcadas: Optional[Dict[str, float]] = None
    status: Optional[str] = Field(None, max_length=20)


class UserResponse(UserBase):
    """Schema for User response."""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True