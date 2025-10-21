"""
Procurement models: OrdemCompra.
"""

from sqlalchemy import Column, String, ForeignKey, JSON, DECIMAL, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from shared.database.connection import Base
from shared.models.base import BaseModelMixin


class OrdemCompra(Base, BaseModelMixin):
    """Ordem de Compra model."""

    __tablename__ = "ordens_compra"

    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    numero = Column(String(20), unique=True, nullable=False, index=True)
    solicitante_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    fornecedor_id = Column(UUID(as_uuid=True), ForeignKey("fornecedores.id", ondelete="RESTRICT"), nullable=False)
    valor_total = Column(DECIMAL(15, 2), nullable=False)
    status = Column(String(30), default="rascunho", index=True)  # rascunho, aguardando_aprovacao, aprovada, pedido_emitido, recebido, cancelada
    itens = Column(JSON, nullable=False)  # [{descricao, qtd, valor_unit}]
    aprovadores = Column(JSON)  # [{usuario_id, nivel, aprovado_em}]
    centro_custo = Column(String(50))
    data_entrega_prevista = Column(Date)
    meta_data = Column(JSON)

    # Relationships
    empresa = relationship("Empresa", back_populates="ordens_compra")
    solicitante = relationship("Usuario", back_populates="ordens_compra")
    fornecedor = relationship("Fornecedor", back_populates="ordens_compra")