"""
UserProfile model.
"""

from sqlalchemy import Column, String, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from shared.database.connection import Base
from shared.models.base import BaseModelMixin


class UserProfile(Base, BaseModelMixin):
    """UserProfile model."""

    __tablename__ = "user_profiles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"))
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    position = Column(String(100))
    approval_limits = Column(JSON)  # {financial: 50000, procurement: 30000}
    status = Column(String(20), default="active")

    # Relationships
    company = relationship("Company", back_populates="users")
    department = relationship("Department", back_populates="users")
    corporate_cards = relationship("CorporateCard", back_populates="cardholder")
    purchase_orders = relationship("PurchaseOrder", back_populates="requester")
    tasks = relationship("Task", back_populates="assignee")
    contracts = relationship("Contract", back_populates="responsible")
    approved_transactions = relationship("CardTransaction", back_populates="approver")
    employee = relationship("Employee", back_populates="user", uselist=False)
