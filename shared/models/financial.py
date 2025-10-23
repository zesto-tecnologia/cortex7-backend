"""
Financial models: CostCenter, Supplier, AccountPayable, CorporateCard, CardInvoice, CardTransaction.
"""

from decimal import Decimal
from sqlalchemy import Column, String, ForeignKey, JSON, DECIMAL, Date, Boolean, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from shared.database.connection import Base
from shared.models.base import BaseModelMixin, UUIDMixin


class CostCenter(Base, BaseModelMixin):
    """Cost Center model."""

    __tablename__ = "cost_centers"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    department = Column(String(50))
    monthly_budget = Column(DECIMAL(15, 2))
    current_spending = Column(DECIMAL(15, 2), default=0)

    # Relationships
    company = relationship("Company", back_populates="cost_centers")


class Supplier(Base, BaseModelMixin):
    """Supplier model."""

    __tablename__ = "suppliers"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    company_name = Column(String(255), nullable=False)
    tax_id = Column(String(14), unique=True, nullable=False, index=True)
    category = Column(String(50))  # IT, Cleaning, Materials
    status = Column(String(20), default="active")
    bank_details = Column(JSON)
    contacts = Column(JSON)  # [{name, email, phone}]
    ratings = Column(JSON)  # Performance history

    # Relationships
    company = relationship("Company", back_populates="suppliers")
    accounts_payable = relationship("AccountPayable", back_populates="supplier")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")


class AccountPayable(Base, BaseModelMixin):
    """Account Payable model."""

    __tablename__ = "accounts_payable"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="SET NULL"))
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"))
    document_number = Column(String(50))
    description = Column(String)
    amount = Column(DECIMAL(15, 2), nullable=False)
    due_date = Column(Date, nullable=False, index=True)
    payment_date = Column(Date)
    status = Column(String(20), default="pending", index=True)  # pending, approved, paid, canceled
    cost_center = Column(String(50))
    category = Column(String(50))  # Materials, Services, Personnel
    meta_data = Column("metadata", JSON)  # installment, payment_method, etc
    priority = Column(Integer, default=5)  # 1=critical, 5=normal, 10=low

    # Relationships
    company = relationship("Company", back_populates="accounts_payable")
    supplier = relationship("Supplier", back_populates="accounts_payable")
    document = relationship("Document", back_populates="accounts_payable")
    card_invoices = relationship("CardInvoice", back_populates="account_payable")


class CorporateCard(Base, BaseModelMixin):
    """Corporate Card model."""

    __tablename__ = "corporate_cards"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    cardholder_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="SET NULL"), index=True)
    masked_number = Column(String(20), nullable=False)  # **** **** **** 1234
    brand = Column("card_brand", String(20), nullable=False)  # Still need mapping as DB has card_brand
    card_type = Column("type", String(20), default="corporate")  # Still need mapping as DB has type
    credit_limit = Column(DECIMAL(15, 2))
    available_limit = Column("available_credit", DECIMAL(15, 2))  # Still need mapping as DB has available_credit
    invoice_due_day = Column(Integer)  # Day of month (e.g., 10)
    status = Column(String(20), default="active")  # active, blocked, canceled
    default_cost_center = Column(String(50))
    department = Column(String(50))  # Now using English column name
    meta_data = Column("metadata", JSON)  # Keep mapping as metadata is reserved

    # Relationships
    company = relationship("Company", back_populates="corporate_cards")
    cardholder = relationship("UserProfile", back_populates="corporate_cards")
    invoices = relationship("CardInvoice", back_populates="card", cascade="all, delete-orphan")
    transactions = relationship("CardTransaction", back_populates="card", cascade="all, delete-orphan")


class CardInvoice(Base, BaseModelMixin):
    """Corporate Card Invoice model."""

    __tablename__ = "card_invoices"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    card_id = Column(UUID(as_uuid=True), ForeignKey("corporate_cards.id", ondelete="CASCADE"),
                      nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"))  # Now using English column name
    reference = Column(String(7), nullable=False)  # MM/YYYY (e.g., 10/2025)
    closing_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False, index=True)
    total_amount = Column(DECIMAL(15, 2), nullable=False)
    paid_amount = Column(DECIMAL(15, 2), default=0)
    status = Column(String(20), default="open", index=True)  # open, partially_paid, paid, overdue, disputed
    account_payable_id = Column(UUID(as_uuid=True), ForeignKey("accounts_payable.id", ondelete="SET NULL"))
    notes = Column(String)
    meta_data = Column("metadata", JSON)  # Map to database column metadata

    # Constraints
    __table_args__ = (
        UniqueConstraint('card_id', 'reference', name='_card_reference_uc'),
    )

    # Relationships
    company = relationship("Company", back_populates="card_invoices")
    card = relationship("CorporateCard", back_populates="invoices")
    document = relationship("Document", back_populates="card_invoices")
    account_payable = relationship("AccountPayable", back_populates="card_invoices")
    transactions = relationship("CardTransaction", back_populates="invoice", cascade="all, delete-orphan")


class CardTransaction(Base, BaseModelMixin):
    """Corporate Card Transaction model."""

    __tablename__ = "card_transactions"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("card_invoices.id", ondelete="CASCADE"),
                      nullable=False, index=True)
    card_id = Column(UUID(as_uuid=True), ForeignKey("corporate_cards.id", ondelete="CASCADE"),
                      nullable=False, index=True)
    transaction_date = Column(Date, nullable=False, index=True)
    posting_date = Column(Date, nullable=False)  # Date appearing on invoice
    merchant = Column(String(255), nullable=False)
    category = Column(String(50), index=True)  # Food, Transportation, Software, Lodging
    description = Column(String)
    amount = Column(DECIMAL(15, 2), nullable=False)
    usd_amount = Column(DECIMAL(15, 2))  # Now using English column name
    exchange_rate = Column(DECIMAL(10, 4))  # Now using English column name
    currency = Column(String(3), default="BRL")
    installment = Column(String(10))  # "1/3", "2/3" if installment
    cost_center = Column(String(50))
    project = Column(String(100))  # If linked to specific project
    approved = Column(Boolean, default=False, index=True)
    approver_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="SET NULL"))
    approved_at = Column(Date)
    justification = Column(String)  # Expense justification
    receipt_url = Column(String(500))  # Link to receipt/invoice
    disputed = Column(Boolean, default=False)  # Now using English column name
    dispute_reason = Column(String)  # Now using English column name
    meta_data = Column("metadata", JSON)  # Map to database column metadata

    # Relationships
    company = relationship("Company", back_populates="card_transactions")
    invoice = relationship("CardInvoice", back_populates="transactions")
    card = relationship("CorporateCard", back_populates="transactions")
    approver = relationship("UserProfile", back_populates="approved_transactions")
