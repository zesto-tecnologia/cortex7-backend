"""RefreshToken model for managing refresh tokens."""

from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from services.auth.database import Base
from services.auth.models.base import TimestampMixin


class RefreshToken(Base, TimestampMixin):
    """Refresh token model for JWT token management."""

    __tablename__ = "refresh_tokens"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    token_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    token_family_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    device_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    def is_valid(self) -> bool:
        """Check if the refresh token is valid."""
        return not self.revoked and self.expires_at > datetime.now(timezone.utc)

    def revoke(self) -> None:
        """Revoke the refresh token."""
        self.revoked = True

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at}, revoked={self.revoked})>"