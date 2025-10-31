"""
Workflow and Task models.
"""

from sqlalchemy import Column, String, ForeignKey, JSON, Boolean, Integer, Date, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from shared.database.connection import Base
from shared.models.base import BaseModelMixin, UUIDMixin


class CorporateWorkflow(Base, BaseModelMixin):
    """Corporate Workflow model."""

    __tablename__ = "corporate_workflows"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    workflow_type = Column(String(50), nullable=False, index=True)  # hiring, purchase, contract_approval
    name = Column(String(255), nullable=False)
    phases = Column(JSON, nullable=False)  # [{name, order, responsible, actions}]
    active = Column(Boolean, default=True)

    # Relationships
    company = relationship("Company", back_populates="workflows")
    tasks = relationship("Task", back_populates="workflow")


class Task(Base, BaseModelMixin):
    """Task model."""
    __tablename__ = "tasks"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("corporate_workflows.id", ondelete="SET NULL"))
    entity_type = Column(String(50))  # purchase_order, contract, employee
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="SET NULL"), index=True)
    department = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")  # pending, in_progress, blocked, completed, canceled
    priority = Column(Integer, default=5)  # 1=critical to 10=low
    due_date = Column(Date)
    legal_deadline = Column(Boolean, default=False)  # True if has legal implication
    days_until_due = Column(Integer)  # Calculated automatically
    dependencies = Column(ARRAY(UUID(as_uuid=True)))  # IDs of other blocking tasks
    meta_data = Column(JSON)
    completed_at = Column(Date)

    # Relationships
    company = relationship("Company", back_populates="tasks")
    workflow = relationship("CorporateWorkflow", back_populates="tasks")
    assignee = relationship("UserProfile", back_populates="tasks")

    # Indexes are defined in the database using CREATE INDEX statements
