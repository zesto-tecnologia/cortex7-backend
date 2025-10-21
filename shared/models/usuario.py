"""
Usuario model.
"""

from sqlalchemy import Column, String, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from shared.database.connection import Base
from shared.models.base import BaseModelMixin


class Usuario(Base, BaseModelMixin):
    """Usuario model."""

    __tablename__ = "usuarios"

    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    departamento_id = Column(UUID(as_uuid=True), ForeignKey("departamentos.id", ondelete="SET NULL"))
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    cargo = Column(String(100))
    alcadas = Column(JSON)  # {financeiro: 50000, suprimentos: 30000}
    status = Column(String(20), default="ativo")

    # Relationships
    empresa = relationship("Empresa", back_populates="usuarios")
    departamento = relationship("Departamento", back_populates="usuarios")
    cartoes = relationship("CartaoCorporativo", back_populates="portador")
    ordens_compra = relationship("OrdemCompra", back_populates="solicitante")
    tarefas = relationship("Tarefa", back_populates="responsavel")
    contratos = relationship("Contrato", back_populates="responsavel")
    lancamentos_aprovados = relationship("LancamentoCartao", back_populates="aprovador")
    funcionario = relationship("Funcionario", back_populates="usuario", uselist=False)