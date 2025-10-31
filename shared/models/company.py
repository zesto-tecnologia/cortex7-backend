"""
Company and Department models.
"""

from sqlalchemy import Column, String, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from shared.database.connection import Base
from shared.models.base import BaseModelMixin, UUIDMixin


class Company(Base, BaseModelMixin):
    """Company model."""

    __tablename__ = "companies"

    company_name = Column(String(255), nullable=False)
    tax_id = Column(String(14), unique=True, nullable=False, index=True)
    settings = Column(JSON)

    # Relationships
    departments = relationship("Department", back_populates="company", cascade="all, delete-orphan")
    users = relationship("UserProfile", back_populates="company", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="company", cascade="all, delete-orphan")
    cost_centers = relationship("CostCenter", back_populates="company", cascade="all, delete-orphan")
    suppliers = relationship("Supplier", back_populates="company", cascade="all, delete-orphan")
    accounts_payable = relationship("AccountPayable", back_populates="company", cascade="all, delete-orphan")
    corporate_cards = relationship("CorporateCard", back_populates="company", cascade="all, delete-orphan")
    card_invoices = relationship("CardInvoice", back_populates="company", cascade="all, delete-orphan")
    card_transactions = relationship("CardTransaction", back_populates="company", cascade="all, delete-orphan")
    employees = relationship("Employee", back_populates="company", cascade="all, delete-orphan")
    contracts = relationship("Contract", back_populates="company", cascade="all, delete-orphan")
    lawsuits = relationship("Lawsuit", back_populates="company", cascade="all, delete-orphan")
    purchase_orders = relationship("PurchaseOrder", back_populates="company", cascade="all, delete-orphan")
    workflows = relationship("CorporateWorkflow", back_populates="company", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="company", cascade="all, delete-orphan")


class Department(Base, UUIDMixin):
    """Department model."""

    __tablename__ = "departments"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    meta_data = Column("metadata", JSON)  # Use different attribute name, map to 'metadata' column

    # Relationships
    company = relationship("Company", back_populates="departments")
    users = relationship("UserProfile", back_populates="department")
    employees = relationship("Employee", back_populates="department")
