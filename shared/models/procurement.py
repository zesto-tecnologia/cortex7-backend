"""
Procurement models: PurchaseOrder.
"""

from sqlalchemy import Column, String, ForeignKey, JSON, DECIMAL, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from shared.database.connection import Base
from shared.models.base import BaseModelMixin


class PurchaseOrder(Base, BaseModelMixin):
    """Purchase Order model."""

    __tablename__ = "purchase_orders"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    number = Column(String(20), unique=True, nullable=False, index=True)
    requester_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="RESTRICT"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False)
    total_amount = Column(DECIMAL(15, 2), nullable=False)
    status = Column(String(30), default="draft", index=True)  # draft, pending_approval, approved, order_placed, received, canceled
    items = Column(JSON, nullable=False)  # [{description, qty, unit_price}]
    approvers = Column(JSON)  # [{user_id, level, approved_at}]
    cost_center = Column(String(50))
    expected_delivery_date = Column(Date)
    meta_data = Column("metadata", JSON)  # Map to database column name

    # Relationships
    company = relationship("Company", back_populates="purchase_orders")
    requester = relationship("UserProfile", back_populates="purchase_orders")
    supplier = relationship("Supplier", back_populates="purchase_orders")
