"""
Audit and logging models.
"""

from sqlalchemy import Column, String, ForeignKey, JSON, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from shared.database.connection import Base
from shared.models.base import BaseModelMixin, UUIDMixin


class AgentLog(Base, BaseModelMixin):
    """Agent Log model."""

    __tablename__ = "agent_logs"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    agent_type = Column(String(50), nullable=False, index=True)  # ranker, generator, actuator, validator, extractor, conversational, orchestrator
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))  # task, document, purchase_order
    entity_id = Column(UUID(as_uuid=True))
    input_data = Column(JSON)  # What was sent to the agent
    output_data = Column(JSON)  # What the agent returned
    success = Column(Boolean, default=True)
    execution_time_ms = Column(Integer)
    error = Column(String)

    # Relationships
    company = relationship("Company")


class AuditTrail(Base, BaseModelMixin):
    """Audit Trail model."""

    __tablename__ = "audit_trail"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="SET NULL"))
    table_name = Column(String(50), nullable=False, index=True)
    record_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    action = Column(String(20), nullable=False)  # INSERT, UPDATE, DELETE
    previous_data = Column(JSON)
    new_data = Column(JSON)
    ip_address = Column(INET)

    # Relationships
    company = relationship("Company")
    user = relationship("UserProfile")


class EmbeddingCache(Base, BaseModelMixin):
    """Embedding Cache model."""

    __tablename__ = "embedding_cache"

    text = Column(String, nullable=False)
    hash = Column(String(64), unique=True, nullable=False, index=True)  # Text hash
    embedding = Column(Vector(1536), nullable=False)
    model = Column(String(50), default="text-embedding-ada-002")


class AgentConfig(Base, BaseModelMixin):
    """Agent Configuration model."""

    __tablename__ = "agent_configs"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    agent_type = Column(String(50), nullable=False, index=True)
    configuration = Column(JSON, nullable=False)
    active = Column(Boolean, default=True)

    # Relationships
    company = relationship("Company")
