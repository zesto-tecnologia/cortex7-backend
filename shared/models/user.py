"""
UserProfile model - Corporate user profile linked to auth service users.

This model creates a many-to-one relationship with the auth service's User model.
Each auth user can have one corporate profile with company-specific information.
"""

from typing import Optional
from uuid import UUID
from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from shared.database.connection import Base
from shared.models.base import BaseModelMixin


class UserProfile(Base, BaseModelMixin):
    """
    Corporate user profile with company-specific information.

    Links to the auth service's users table via user_id foreign key.
    This is a cross-service relationship managed at the database level.
    """

    __tablename__ = "user_profiles"
    __table_args__ = {"comment": "Corporate user profiles linked to auth users"}

    # Cross-service relationship to auth.users table
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Links to auth users table"
    )

    # Company relationship
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Department relationship (optional)
    department_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True
    )

    # User information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    position: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Business logic fields
    approval_limits: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Approval limits by module: {finance: 50000, procurement: 30000}"
    )
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False, index=True)

    # Relationships (within corporate domain)
    company: Mapped["Company"] = relationship("Company", back_populates="users")
    department: Mapped[Optional["Department"]] = relationship("Department", back_populates="users")
    corporate_cards: Mapped[list["CorporateCard"]] = relationship(
        "CorporateCard",
        back_populates="cardholder"
    )
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="requester"
    )
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="assignee")
    contracts: Mapped[list["Contract"]] = relationship("Contract", back_populates="responsible")
    approved_transactions: Mapped[list["CardTransaction"]] = relationship(
        "CardTransaction",
        back_populates="approver"
    )
    employee: Mapped[Optional["Employee"]] = relationship(
        "Employee",
        back_populates="user",
        uselist=False
    )

    def __repr__(self) -> str:
        return f"<UserProfile(id={self.id}, email={self.email}, company_id={self.company_id})>"
