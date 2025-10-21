"""
RH models: Funcionario and ContratoTrabalho.
"""

from sqlalchemy import Column, String, ForeignKey, JSON, DECIMAL, Date, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from shared.database.connection import Base
from shared.models.base import BaseModelMixin, UUIDMixin


class Funcionario(Base, BaseModelMixin):
    """Funcionario model."""

    __tablename__ = "funcionarios"

    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"))
    cpf = Column(String(11), unique=True, nullable=False, index=True)
    data_nascimento = Column(Date)
    data_admissao = Column(Date, nullable=False)
    data_demissao = Column(Date)
    cargo = Column(String(100), nullable=False)
    departamento_id = Column(UUID(as_uuid=True), ForeignKey("departamentos.id", ondelete="SET NULL"))
    salario = Column(DECIMAL(10, 2))
    tipo_contrato = Column(String(20))  # CLT, PJ, Estagio
    regime_trabalho = Column(String(20))  # Presencial, Remoto, Hibrido
    dados_pessoais = Column(JSON)  # Endereço, contatos emergência
    beneficios = Column(JSON)  # VT, VA, plano saúde
    documentos = Column(JSON)  # Links docs: RG, CPF, carteira trabalho
    ferias = Column(JSON)  # [{periodo_aquisitivo, dias_disponiveis, historico}]
    status = Column(String(20), default="ativo", index=True)

    # Relationships
    empresa = relationship("Empresa", back_populates="funcionarios")
    usuario = relationship("Usuario", back_populates="funcionario")
    departamento = relationship("Departamento", back_populates="funcionarios")
    contratos_trabalho = relationship("ContratoTrabalho", back_populates="funcionario", cascade="all, delete-orphan")


class ContratoTrabalho(Base, BaseModelMixin):
    """Contrato de Trabalho model."""

    __tablename__ = "contratos_trabalho"

    funcionario_id = Column(UUID(as_uuid=True), ForeignKey("funcionarios.id", ondelete="CASCADE"),
                           nullable=False, index=True)
    documento_id = Column(UUID(as_uuid=True), ForeignKey("documentos.id", ondelete="SET NULL"))
    tipo = Column(String(20), nullable=False)  # admissao, alteracao, rescisao
    data_inicio = Column(Date, nullable=False)
    data_fim = Column(Date)
    conteudo = Column(String)  # Texto completo do contrato
    clausulas_especiais = Column(JSON)
    assinado = Column(Boolean, default=False)
    assinatura_funcionario_data = Column(Date)
    assinatura_empresa_data = Column(Date)

    # Relationships
    funcionario = relationship("Funcionario", back_populates="contratos_trabalho")
    documento = relationship("Documento", back_populates="contratos_trabalho")