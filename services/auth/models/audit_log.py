"""AuditLog model for tracking authentication events."""

from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from services.auth.database import Base


class AuditLog(Base):
    """Audit log model for tracking authentication and authorization events."""

    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Event details
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="NOW()",
        nullable=False,
        index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )  # login_success, token_refresh, permission_denied
    result: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )  # success, failure, denied

    # User tracking
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Request metadata
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv6 compatible
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    service_name: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Event details
    event_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Flexible JSON storage

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, event_type={self.event_type}, timestamp={self.timestamp})>"