"""InviteCode model for controlled user registration."""

from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from services.auth.database import Base
from services.auth.models.base import TimestampMixin


class InviteCode(Base, TimestampMixin):
    """Invite code model for controlled user registration."""

    __tablename__ = "invite_codes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True
    )

    # Creator tracking
    creator_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # Timestamps
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Usage tracking
    used_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    # Relationships
    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[creator_id],
        back_populates="created_invites",
        uselist=False  # Single user, not a list
    )
    used_by: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[used_by_id],
        back_populates="used_invite",
        uselist=False  # Single user, not a list
    )

    def is_valid(self) -> bool:
        """Check if invite code is still valid."""
        now = datetime.now(timezone.utc)

        # Ensure expires_at has timezone info for comparison
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        return (
            self.used_at is None
            and self.revoked_at is None
            and expires_at > now
        )

    def revoke(self) -> None:
        """Revoke the invite code."""
        self.revoked_at = datetime.now(timezone.utc)

    def mark_as_used(self, user_id: UUID) -> None:
        """Mark the invite code as used."""
        self.used_at = datetime.now(timezone.utc)
        self.used_by_id = user_id

    def __repr__(self) -> str:
        return f"<InviteCode(id={self.id}, code={self.code}, used={self.used_at is not None})>"
