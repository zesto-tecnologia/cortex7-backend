"""
Base model mixins for common fields.
"""

from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class UUIDMixin:
    """Mixin for UUID primary key using SQLAlchemy 2.0 syntax."""

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps using SQLAlchemy 2.0 syntax."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class BaseModelMixin(UUIDMixin, TimestampMixin):
    """Base mixin combining UUID and timestamps."""
    pass