"""
Document model with vector embeddings.
"""

from sqlalchemy import Column, String, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from shared.database.connection import Base
from shared.models.base import BaseModelMixin


class Document(Base, BaseModelMixin):
    """Document model with vector embeddings for semantic search."""

    __tablename__ = "documents"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    department = Column(String(50), nullable=False)  # legal, financial, hr, procurement
    type = Column(String(50), nullable=False, index=True)  # contract, invoice, resume, policy
    title = Column(String(255))
    original_content = Column(Text)  # Extracted text
    meta_data = Column("metadata", JSON, nullable=False)  # Extracted structured data
    file_url = Column(String(500))  # S3/Storage link
    embedding = Column(Vector(1536))  # OpenAI ada-002 or similar
    status = Column(String(20), default="active")

    # Relationships
    company = relationship("Company", back_populates="documents")
    accounts_payable = relationship("AccountPayable", back_populates="document")
    card_invoices = relationship("CardInvoice", back_populates="document")
    employment_contracts = relationship("EmploymentContract", back_populates="document")
    contracts = relationship("Contract", back_populates="document")
