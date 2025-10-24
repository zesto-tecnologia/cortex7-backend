"""
Database models for the Cortex system.
Import all models here for Alembic to detect them.
"""

from shared.models.company import Company, Department
from shared.models.user import UserProfile
from shared.models.document import Document
from shared.models.financial import (
    CostCenter,
    Supplier,
    AccountPayable,
    CorporateCard,
    CardInvoice,
    CardTransaction,
)
from shared.models.hr import Employee, EmploymentContract
from shared.models.legal import Contract, Lawsuit
from shared.models.procurement import PurchaseOrder
from shared.models.workflow import CorporateWorkflow, Task
from shared.models.audit import AgentLog, AuditTrail, EmbeddingCache, AgentConfig

__all__ = [
    # Company
    "Company",
    "Department",
    # User
    "UserProfile",
    # Document
    "Document",
    # Financial
    "CostCenter",
    "Supplier",
    "AccountPayable",
    "CorporateCard",
    "CardInvoice",
    "CardTransaction",
    # HR
    "Employee",
    "EmploymentContract",
    # Legal
    "Contract",
    "Lawsuit",
    # Procurement
    "PurchaseOrder",
    # Workflow
    "CorporateWorkflow",
    "Task",
    # Audit
    "AgentLog",
    "AuditTrail",
    "EmbeddingCache",
    "AgentConfig",
]
