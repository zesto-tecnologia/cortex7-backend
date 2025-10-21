"""
Documento model with vector embeddings.
"""

from sqlalchemy import Column, String, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from shared.database.connection import Base
from shared.models.base import BaseModelMixin


class Documento(Base, BaseModelMixin):
    """Documento model with vector embeddings for semantic search."""

    __tablename__ = "documentos"

    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    departamento = Column(String(50), nullable=False)  # juridico, financeiro, rh, suprimentos
    tipo = Column(String(50), nullable=False, index=True)  # contrato, nota_fiscal, curriculo, politica
    titulo = Column(String(255))
    conteudo_original = Column(Text)  # Texto extraído
    meta_data = Column(JSON, nullable=False)  # Dados estruturados extraídos
    arquivo_url = Column(String(500))  # Link S3/Storage
    embedding = Column(Vector(1536))  # OpenAI ada-002 or similar
    status = Column(String(20), default="ativo")

    # Relationships
    empresa = relationship("Empresa", back_populates="documentos")
    contas_pagar = relationship("ContaPagar", back_populates="documento")
    faturas_cartao = relationship("FaturaCartao", back_populates="documento")
    contratos_trabalho = relationship("ContratoTrabalho", back_populates="documento")
    contratos = relationship("Contrato", back_populates="documento")