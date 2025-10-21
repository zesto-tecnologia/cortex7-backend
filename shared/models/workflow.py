"""
Workflow and Task models.
"""

from sqlalchemy import Column, String, ForeignKey, JSON, Boolean, Integer, Date, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from shared.database.connection import Base
from shared.models.base import BaseModelMixin, UUIDMixin


class Workflow(Base, BaseModelMixin):
    """Workflow model."""

    __tablename__ = "workflows"

    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    tipo = Column(String(50), nullable=False, index=True)  # contratacao, compra, aprovacao_contrato
    nome = Column(String(255), nullable=False)
    fases = Column(JSON, nullable=False)  # [{nome, ordem, responsavel, acoes}]
    ativo = Column(Boolean, default=True)

    # Relationships
    empresa = relationship("Empresa", back_populates="workflows")
    tarefas = relationship("Tarefa", back_populates="workflow")


class Tarefa(Base, BaseModelMixin):
    """Tarefa model."""
    __tablename__ = "tarefas"

    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="SET NULL"))
    entidade_tipo = Column(String(50))  # ordem_compra, contrato, funcionario
    entidade_id = Column(UUID(as_uuid=True), nullable=False)
    titulo = Column(String(255), nullable=False)
    descricao = Column(String)
    responsavel_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), index=True)
    departamento = Column(String(50), nullable=False)
    status = Column(String(20), default="pendente")  # pendente, em_andamento, bloqueada, concluida, cancelada
    prioridade = Column(Integer, default=5)  # 1=crítico até 10=baixo
    prazo = Column(Date)
    prazo_legal = Column(Boolean, default=False)  # True se tem implicação legal
    dias_para_vencimento = Column(Integer)  # Calculado automaticamente
    dependencias = Column(ARRAY(UUID(as_uuid=True)))  # IDs de outras tarefas que bloqueiam esta
    meta_data = Column(JSON)
    concluida_em = Column(Date)

    # Relationships
    empresa = relationship("Empresa", back_populates="tarefas")
    workflow = relationship("Workflow", back_populates="tarefas")
    responsavel = relationship("Usuario", back_populates="tarefas")

    # Indexes are defined in the database using CREATE INDEX statements
