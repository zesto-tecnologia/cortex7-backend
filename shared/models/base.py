"""
Base model mixins for common fields.
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid


class UUIDMixin:
    """Mixin for UUID primary key."""

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class BaseModelMixin(UUIDMixin, TimestampMixin):
    """Base mixin combining UUID and timestamps."""
    pass