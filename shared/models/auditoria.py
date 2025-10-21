"""
Audit and logging models.
"""

from sqlalchemy import Column, String, ForeignKey, JSON, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from shared.database.connection import Base
from shared.models.base import BaseModelMixin, UUIDMixin


class LogAgente(Base, BaseModelMixin):
    """Log de Agentes model."""

    __tablename__ = "logs_agentes"

    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"))
    agente_tipo = Column(String(50), nullable=False, index=True)  # ranqueador, gerador, atuador, validador, extrator, conversacional, orquestrador
    acao = Column(String(100), nullable=False)
    entidade_tipo = Column(String(50))  # tarefa, documento, ordem_compra
    entidade_id = Column(UUID(as_uuid=True))
    input = Column(JSON)  # O que foi enviado ao agente
    output = Column(JSON)  # O que o agente retornou
    sucesso = Column(Boolean, default=True)
    tempo_execucao_ms = Column(Integer)
    erro = Column(String)

    # Relationships
    empresa = relationship("Empresa")


class Auditoria(Base, BaseModelMixin):
    """Auditoria model."""

    __tablename__ = "auditoria"

    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"))
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"))
    tabela = Column(String(50), nullable=False, index=True)
    registro_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    acao = Column(String(20), nullable=False)  # INSERT, UPDATE, DELETE
    dados_anteriores = Column(JSON)
    dados_novos = Column(JSON)
    ip_address = Column(INET)

    # Relationships
    empresa = relationship("Empresa")
    usuario = relationship("Usuario")


class CacheEmbedding(Base, BaseModelMixin):
    """Cache de Embeddings model."""

    __tablename__ = "cache_embeddings"

    texto = Column(String, nullable=False)
    hash = Column(String(64), unique=True, nullable=False, index=True)  # Hash do texto
    embedding = Column(Vector(1536), nullable=False)
    modelo = Column(String(50), default="text-embedding-ada-002")


class AgenteConfig(Base, BaseModelMixin):
    """Configuração de Agentes model."""

    __tablename__ = "agentes_config"

    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"))
    agente_tipo = Column(String(50), nullable=False, index=True)
    configuracao = Column(JSON, nullable=False)
    ativo = Column(Boolean, default=True)

    # Relationships
    empresa = relationship("Empresa")