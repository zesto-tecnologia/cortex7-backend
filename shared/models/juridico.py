"""
Legal models: Contrato and ProcessoJuridico.
"""

from sqlalchemy import Column, String, ForeignKey, JSON, DECIMAL, Date, Boolean, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from shared.database.connection import Base
from shared.models.base import BaseModelMixin, UUIDMixin


class Contrato(Base, BaseModelMixin):
    """Contrato jurídico model."""

    __tablename__ = "contratos"

    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    documento_id = Column(UUID(as_uuid=True), ForeignKey("documentos.id", ondelete="SET NULL"))
    tipo = Column(String(50), nullable=False)  # fornecedor, cliente, parceria, trabalhista
    parte_contraria = Column(String(255), nullable=False)
    cnpj_cpf_contraparte = Column(String(14))
    objeto = Column(String, nullable=False)  # Descrição do contrato
    valor = Column(DECIMAL(15, 2))
    data_inicio = Column(Date, nullable=False, index=True)
    data_fim = Column(Date, index=True)
    renovacao_automatica = Column(Boolean, default=False)
    status = Column(String(20), default="vigente", index=True)  # rascunho, aprovacao, vigente, rescindido, encerrado, vencido
    clausulas_criticas = Column(JSON)  # Multas, SLAs, confidencialidade
    prazos_importantes = Column(JSON)  # [{descricao, data, notificado}]
    responsavel_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"))
    meta_data = Column(JSON)

    # Relationships
    empresa = relationship("Empresa", back_populates="contratos")
    documento = relationship("Documento", back_populates="contratos")
    responsavel = relationship("Usuario", back_populates="contratos")


class ProcessoJuridico(Base, BaseModelMixin):
    """Processo Jurídico model."""

    __tablename__ = "processos_juridicos"

    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    numero_processo = Column(String(50), unique=True, index=True)
    tipo = Column(String(50))  # trabalhista, civel, tributario
    parte_contraria = Column(String(255))
    valor_causa = Column(DECIMAL(15, 2))
    status = Column(String(30))  # andamento, suspenso, concluido
    risco = Column(String(20))  # baixo, medio, alto
    tribunal = Column(String(100))
    advogado_responsavel = Column(String(255))
    historico = Column(JSON)  # [{data, evento, descricao}]
    proxima_acao = Column(Date, index=True)
    proxima_acao_descricao = Column(String)
    documentos_ids = Column(ARRAY(UUID(as_uuid=True)))  # Array de IDs de documentos

    # Relationships
    empresa = relationship("Empresa", back_populates="processos_juridicos")