"""
Empresa and Departamento models.
"""

from sqlalchemy import Column, String, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from shared.database.connection import Base
from shared.models.base import BaseModelMixin, UUIDMixin


class Empresa(Base, BaseModelMixin):
    """Empresa model."""

    __tablename__ = "empresas"

    razao_social = Column(String(255), nullable=False)
    cnpj = Column(String(14), unique=True, nullable=False, index=True)
    configuracoes = Column(JSON)

    # Relationships
    departamentos = relationship("Departamento", back_populates="empresa", cascade="all, delete-orphan")
    usuarios = relationship("Usuario", back_populates="empresa", cascade="all, delete-orphan")
    documentos = relationship("Documento", back_populates="empresa", cascade="all, delete-orphan")
    centros_custo = relationship("CentroCusto", back_populates="empresa", cascade="all, delete-orphan")
    fornecedores = relationship("Fornecedor", back_populates="empresa", cascade="all, delete-orphan")
    contas_pagar = relationship("ContaPagar", back_populates="empresa", cascade="all, delete-orphan")
    cartoes = relationship("CartaoCorporativo", back_populates="empresa", cascade="all, delete-orphan")
    faturas_cartao = relationship("FaturaCartao", back_populates="empresa", cascade="all, delete-orphan")
    lancamentos_cartao = relationship("LancamentoCartao", back_populates="empresa", cascade="all, delete-orphan")
    funcionarios = relationship("Funcionario", back_populates="empresa", cascade="all, delete-orphan")
    contratos = relationship("Contrato", back_populates="empresa", cascade="all, delete-orphan")
    processos_juridicos = relationship("ProcessoJuridico", back_populates="empresa", cascade="all, delete-orphan")
    ordens_compra = relationship("OrdemCompra", back_populates="empresa", cascade="all, delete-orphan")
    workflows = relationship("Workflow", back_populates="empresa", cascade="all, delete-orphan")
    tarefas = relationship("Tarefa", back_populates="empresa", cascade="all, delete-orphan")


class Departamento(Base, UUIDMixin):
    """Departamento model."""

    __tablename__ = "departamentos"

    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    nome = Column(String(100), nullable=False)
    meta_data = Column(JSON)

    # Relationships
    empresa = relationship("Empresa", back_populates="departamentos")
    usuarios = relationship("Usuario", back_populates="departamento")
    funcionarios = relationship("Funcionario", back_populates="departamento")