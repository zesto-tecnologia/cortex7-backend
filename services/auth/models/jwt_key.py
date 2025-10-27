"""JWTKey model for managing JWT signing keys."""

from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from services.auth.database import Base
from services.auth.models.base import TimestampMixin


class JWTKey(Base, TimestampMixin):
    """JWT signing key model for key rotation management."""

    __tablename__ = "jwt_keys"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    kid: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    private_key_ref: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Reference to private key in Vault/Secrets Manager"
    )
    algorithm: Mapped[str] = mapped_column(
        String(10),
        default="RS256",
        nullable=False
    )
    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )

    def is_valid(self) -> bool:
        """Check if the key is valid for use."""
        return self.active and self.expires_at > datetime.now(timezone.utc)

    def deactivate(self) -> None:
        """Deactivate the key."""
        self.active = False

    def __repr__(self) -> str:
        return f"<JWTKey(id={self.id}, kid={self.kid}, active={self.active}, expires_at={self.expires_at})>"