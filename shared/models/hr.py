"""
HR models: Employee and EmploymentContract.
"""

from sqlalchemy import Column, String, ForeignKey, JSON, DECIMAL, Date, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from shared.database.connection import Base
from shared.models.base import BaseModelMixin, UUIDMixin


class Employee(Base, BaseModelMixin):
    """Employee model."""

    __tablename__ = "employees"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="SET NULL"))
    tax_id = Column(String(11), unique=True, nullable=False, index=True)
    birth_date = Column(Date)
    hire_date = Column(Date, nullable=False)
    termination_date = Column(Date)
    position = Column(String(100), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"))
    salary = Column(DECIMAL(10, 2))
    contract_type = Column(String(20))  # CLT, Contractor, Intern
    work_mode = Column(String(20))  # On-site, Remote, Hybrid
    personal_data = Column(JSON)  # Address, emergency contacts
    benefits = Column(JSON)  # Transportation, meal allowance, health insurance
    documents = Column(JSON)  # Links to docs: ID, tax ID, work card
    vacation = Column(JSON)  # [{accrual_period, available_days, history}]
    status = Column(String(20), default="active", index=True)

    # Relationships
    company = relationship("Company", back_populates="employees")
    user = relationship("UserProfile", back_populates="employee")
    department = relationship("Department", back_populates="employees")
    employment_contracts = relationship("EmploymentContract", back_populates="employee", cascade="all, delete-orphan")


class EmploymentContract(Base, BaseModelMixin):
    """Employment Contract model."""

    __tablename__ = "employment_contracts"

    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"),
                           nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"))  # Now using English column name
    contract_type = Column(String(20), nullable=False)  # hire, amendment, termination
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    content = Column(String)  # Full contract text
    special_clauses = Column(JSON)
    signed = Column(Boolean, default=False)
    employee_signature_date = Column(Date)
    company_signature_date = Column(Date)

    # Relationships
    employee = relationship("Employee", back_populates="employment_contracts")
    document = relationship("Document", back_populates="employment_contracts")
