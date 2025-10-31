"""
Legal models: Contract and Lawsuit.
"""

from sqlalchemy import Column, String, ForeignKey, JSON, DECIMAL, Date, Boolean, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from shared.database.connection import Base
from shared.models.base import BaseModelMixin


class Contract(Base, BaseModelMixin):
    """Legal Contract model."""

    __tablename__ = "contracts"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"))  # Now using English column name
    contract_type = Column(String(50), nullable=False)  # supplier, client, partnership, employment
    counterparty = Column(String(255), nullable=False)
    counterparty_tax_id = Column(String(14))
    subject = Column(String, nullable=False)  # Contract description
    amount = Column(DECIMAL(15, 2))
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, index=True)
    auto_renewal = Column(Boolean, default=False)
    status = Column(String(20), default="active", index=True)  # draft, pending_approval, active, terminated, expired, ended
    critical_clauses = Column(JSON)  # Penalties, SLAs, confidentiality
    important_dates = Column(JSON)  # [{description, date, notified}]
    responsible_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="SET NULL"))
    meta_data = Column("metadata", JSON)  # Map to database column metadata

    # Relationships
    company = relationship("Company", back_populates="contracts")
    document = relationship("Document", back_populates="contracts")
    responsible = relationship("UserProfile", back_populates="contracts")


class Lawsuit(Base, BaseModelMixin):
    """Lawsuit model."""

    __tablename__ = "lawsuits"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    case_number = Column(String(50), unique=True, index=True)
    lawsuit_type = Column(String(50))  # labor, civil, tax
    counterparty = Column(String(255))
    cause_amount = Column(DECIMAL(15, 2))
    status = Column(String(30))  # active, suspended, concluded
    risk = Column(String(20))  # low, medium, high
    court = Column(String(100))
    responsible_attorney = Column(String(255))
    history = Column(JSON)  # [{date, event, description}]
    next_action = Column(Date, index=True)
    next_action_description = Column(String)
    document_ids = Column(ARRAY(UUID(as_uuid=True)))  # Array of document IDs

    # Relationships
    company = relationship("Company", back_populates="lawsuits")
