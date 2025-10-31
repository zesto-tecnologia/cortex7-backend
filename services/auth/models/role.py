"""Role and Permission models for RBAC (Role-Based Access Control)."""

from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Text, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from services.auth.database import Base
from services.auth.models.base import TimestampMixin


class Role(Base, TimestampMixin):
    """Role model for RBAC."""

    __tablename__ = "roles"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )  # admin, manager, user
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole",
        back_populates="role",
        cascade="all, delete-orphan"
    )
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles"
    )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name})>"


class Permission(Base, TimestampMixin):
    """Permission model for fine-grained access control."""

    __tablename__ = "permissions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )  # "read:users", "delete:posts"
    resource: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )  # "users", "posts"
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )  # "read", "write", "delete"
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions"
    )

    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, name={self.name})>"


class UserRole(Base):
    """Junction table for User-Role many-to-many relationship."""

    __tablename__ = "user_roles"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="NOW()",
        nullable=False
    )
    assigned_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="user_roles")
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")
    assigner: Mapped["User"] = relationship(
        "User",
        foreign_keys=[assigned_by],
        uselist=False  # Single user, not a list
    )

    def __repr__(self) -> str:
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"


# Association table for Role-Permission many-to-many
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', ForeignKey('roles.id', ondelete="CASCADE"), primary_key=True),
    Column('permission_id', ForeignKey('permissions.id', ondelete="CASCADE"), primary_key=True),
    Column('assigned_at', DateTime(timezone=True), server_default="NOW()", nullable=False)
)
