"""UserCompany model for user-company associations."""

from uuid import UUID
from datetime import datetime
from sqlalchemy import ForeignKey, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from services.auth.database import Base


class UserCompany(Base):
    """Association table for users and companies."""

    __tablename__ = "user_companies"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        index=True
    )
    company_id: Mapped[UUID] = mapped_column(
        primary_key=True,
        index=True
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="NOW()",
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="companies")

    def __repr__(self) -> str:
        return f"<UserCompany(user_id={self.user_id}, company_id={self.company_id}, is_primary={self.is_primary})>"