"""User model for authentication service."""

from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Enum as SQLEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from services.auth.database import Base
from services.auth.models.base import TimestampMixin, SoftDeleteMixin


class User(Base, TimestampMixin, SoftDeleteMixin):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(
        SQLEnum('user', 'admin', 'super_admin', name='user_role'),
        default='user',
        nullable=False
    )
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    auth_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default=None)

    # Relationships
    companies: Mapped[list["UserCompany"]] = relationship(
        "UserCompany",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user"
    )
    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole",
        foreign_keys="[UserRole.user_id]",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    created_invites: Mapped[list["InviteCode"]] = relationship(
        "InviteCode",
        foreign_keys="[InviteCode.creator_id]",
        back_populates="creator"
    )
    used_invite: Mapped["InviteCode"] = relationship(
        "InviteCode",
        foreign_keys="[InviteCode.used_by_id]",
        back_populates="used_by",
        uselist=False
    )

    def is_active(self) -> bool:
        """Check if the user account is active."""
        return self.email_verified and not self.is_deleted()

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"