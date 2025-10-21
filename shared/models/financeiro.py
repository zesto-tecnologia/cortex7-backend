"""
Financial models: CentroCusto, Fornecedor, ContaPagar, Cartoes, Faturas, Lancamentos.
"""

from decimal import Decimal
from sqlalchemy import Column, String, ForeignKey, JSON, DECIMAL, Date, Boolean, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from shared.database.connection import Base
from shared.models.base import BaseModelMixin, UUIDMixin


class CentroCusto(Base, UUIDMixin):
    """Centro de Custo model."""

    __tablename__ = "centros_custo"

    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    codigo = Column(String(20), unique=True, nullable=False, index=True)
    nome = Column(String(100), nullable=False)
    departamento = Column(String(50))
    orcamento_mensal = Column(DECIMAL(15, 2))
    gasto_atual = Column(DECIMAL(15, 2), default=0)

    # Relationships
    empresa = relationship("Empresa", back_populates="centros_custo")


class Fornecedor(Base, BaseModelMixin):
    """Fornecedor model."""

    __tablename__ = "fornecedores"

    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    razao_social = Column(String(255), nullable=False)
    cnpj = Column(String(14), unique=True, nullable=False, index=True)
    categoria = Column(String(50))  # TI, Limpeza, Materiais
    status = Column(String(20), default="ativo")
    dados_bancarios = Column(JSON)
    contatos = Column(JSON)  # [{nome, email, telefone}]
    avaliacoes = Column(JSON)  # Histórico de performance

    # Relationships
    empresa = relationship("Empresa", back_populates="fornecedores")
    contas_pagar = relationship("ContaPagar", back_populates="fornecedor")
    ordens_compra = relationship("OrdemCompra", back_populates="fornecedor")


class ContaPagar(Base, BaseModelMixin):
    """Conta a Pagar model."""

    __tablename__ = "contas_pagar"

    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    fornecedor_id = Column(UUID(as_uuid=True), ForeignKey("fornecedores.id", ondelete="SET NULL"))
    documento_id = Column(UUID(as_uuid=True), ForeignKey("documentos.id", ondelete="SET NULL"))
    numero_documento = Column(String(50))
    descricao = Column(String)
    valor = Column(DECIMAL(15, 2), nullable=False)
    data_vencimento = Column(Date, nullable=False, index=True)
    data_pagamento = Column(Date)
    status = Column(String(20), default="pendente", index=True)  # pendente, aprovado, pago, cancelado
    centro_custo = Column(String(50))
    categoria = Column(String(50))  # Materiais, Serviços, Pessoal
    meta_data = Column(JSON)  # parcela, forma_pagamento, etc
    prioridade = Column(Integer, default=5)  # 1=crítico, 5=normal, 10=baixo

    # Relationships
    empresa = relationship("Empresa", back_populates="contas_pagar")
    fornecedor = relationship("Fornecedor", back_populates="contas_pagar")
    documento = relationship("Documento", back_populates="contas_pagar")
    faturas_cartao = relationship("FaturaCartao", back_populates="conta_pagar")


class CartaoCorporativo(Base, BaseModelMixin):
    """Cartão Corporativo model."""

    __tablename__ = "cartoes_corporativos"

    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    portador_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), index=True)
    numero_mascarado = Column(String(20), nullable=False)  # **** **** **** 1234
    bandeira = Column(String(20), nullable=False)  # Visa, Master, Amex
    tipo = Column(String(20), default="corporativo")  # corporativo, empresarial
    limite = Column(DECIMAL(15, 2))
    limite_disponivel = Column(DECIMAL(15, 2))
    data_vencimento_fatura = Column(Integer)  # Dia do mês (ex: 10)
    status = Column(String(20), default="ativo")  # ativo, bloqueado, cancelado
    centro_custo_padrao = Column(String(50))
    departamento = Column(String(50))
    meta_data = Column(JSON)  # Dados do banco, taxas, etc

    # Relationships
    empresa = relationship("Empresa", back_populates="cartoes")
    portador = relationship("Usuario", back_populates="cartoes")
    faturas = relationship("FaturaCartao", back_populates="cartao", cascade="all, delete-orphan")
    lancamentos = relationship("LancamentoCartao", back_populates="cartao", cascade="all, delete-orphan")


class FaturaCartao(Base, BaseModelMixin):
    """Fatura de Cartão Corporativo model."""

    __tablename__ = "faturas_cartao"

    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    cartao_id = Column(UUID(as_uuid=True), ForeignKey("cartoes_corporativos.id", ondelete="CASCADE"),
                      nullable=False, index=True)
    documento_id = Column(UUID(as_uuid=True), ForeignKey("documentos.id", ondelete="SET NULL"))
    referencia = Column(String(7), nullable=False)  # MM/YYYY (ex: 10/2025)
    data_fechamento = Column(Date, nullable=False)
    data_vencimento = Column(Date, nullable=False, index=True)
    valor_total = Column(DECIMAL(15, 2), nullable=False)
    valor_pago = Column(DECIMAL(15, 2), default=0)
    status = Column(String(20), default="aberta", index=True)  # aberta, parcialmente_paga, paga, atrasada, contestada
    conta_pagar_id = Column(UUID(as_uuid=True), ForeignKey("contas_pagar.id", ondelete="SET NULL"))
    observacoes = Column(String)
    meta_data = Column(JSON)  # IOF, juros, multas

    # Constraints
    __table_args__ = (
        UniqueConstraint('cartao_id', 'referencia', name='_cartao_referencia_uc'),
    )

    # Relationships
    empresa = relationship("Empresa", back_populates="faturas_cartao")
    cartao = relationship("CartaoCorporativo", back_populates="faturas")
    documento = relationship("Documento", back_populates="faturas_cartao")
    conta_pagar = relationship("ContaPagar", back_populates="faturas_cartao")
    lancamentos = relationship("LancamentoCartao", back_populates="fatura", cascade="all, delete-orphan")


class LancamentoCartao(Base, BaseModelMixin):
    """Lançamento de Cartão Corporativo model."""

    __tablename__ = "lancamentos_cartao"

    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    fatura_id = Column(UUID(as_uuid=True), ForeignKey("faturas_cartao.id", ondelete="CASCADE"),
                      nullable=False, index=True)
    cartao_id = Column(UUID(as_uuid=True), ForeignKey("cartoes_corporativos.id", ondelete="CASCADE"),
                      nullable=False, index=True)
    data_transacao = Column(Date, nullable=False, index=True)
    data_lancamento = Column(Date, nullable=False)  # Data que aparece na fatura
    estabelecimento = Column(String(255), nullable=False)
    categoria = Column(String(50), index=True)  # Alimentacao, Transporte, Software, Hospedagem
    descricao = Column(String)
    valor = Column(DECIMAL(15, 2), nullable=False)
    valor_dolar = Column(DECIMAL(15, 2))  # Se transação internacional
    cotacao_dolar = Column(DECIMAL(10, 4))  # Taxa de conversão
    moeda = Column(String(3), default="BRL")
    parcela = Column(String(10))  # "1/3", "2/3" se parcelado
    centro_custo = Column(String(50))
    projeto = Column(String(100))  # Se vinculado a projeto específico
    aprovado = Column(Boolean, default=False, index=True)
    aprovador_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"))
    aprovado_em = Column(Date)
    justificativa = Column(String)  # Justificativa da despesa
    recibo_url = Column(String(500))  # Link para recibo/nota fiscal
    contestado = Column(Boolean, default=False)
    motivo_contestacao = Column(String)
    meta_data = Column(JSON)  # milhas, cashback, etc

    # Relationships
    empresa = relationship("Empresa", back_populates="lancamentos_cartao")
    fatura = relationship("FaturaCartao", back_populates="lancamentos")
    cartao = relationship("CartaoCorporativo", back_populates="lancamentos")
    aprovador = relationship("Usuario", back_populates="lancamentos_aprovados")