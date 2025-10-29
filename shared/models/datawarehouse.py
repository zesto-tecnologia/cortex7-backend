"""
Data Warehouse models for Financial Analytics.
Star Schema with Fact and Dimension tables for OMIE financial data.
"""

from decimal import Decimal
from datetime import date
from sqlalchemy import Column, String, ForeignKey, JSON, DECIMAL, Date, Boolean, Integer, BigInteger, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from shared.database.connection import Base
from shared.models.base import BaseModelMixin, UUIDMixin


# ============================================================================
# DIMENSION TABLES
# ============================================================================

class DimClient(Base, BaseModelMixin):
    """
    Dimension: Clients/Customers from OMIE.
    Contains all client master data.
    """
    __tablename__ = "dim_clients"

    # Business Keys
    omie_client_id = Column(BigInteger, unique=True, nullable=False, index=True, comment="ID do cliente no OMIE")
    tax_id = Column(String(18), index=True, comment="CPF/CNPJ do cliente")

    # Client Attributes
    legal_name = Column(String(255), comment="Razão social")
    trade_name = Column(String(255), index=True, comment="Nome fantasia")

    # Client Classification (SCD Type 2 ready)
    key_account = Column(String(100), comment="Key Account classification")
    vertical = Column(String(100), comment="Vertical/Segmento")
    pd7_id = Column(String(50), comment="ID interno PD7")
    geo = Column(String(100), comment="Geografia/Região")
    state = Column(String(2), comment="Estado (UF)")

    # Metadata
    source_system = Column(String(50), default="OMIE")
    is_active = Column(Boolean, default=True)
    extra_data = Column(JSON, comment="Dados adicionais do cliente")

    # Relationships
    transactions = relationship("FactFinancialTransaction", back_populates="client")

    __table_args__ = (
        Index('idx_client_tax_id', 'tax_id'),
        Index('idx_client_trade_name', 'trade_name'),
        Index('idx_client_vertical', 'vertical'),
    )


class DimCategory(Base, BaseModelMixin):
    """
    Dimension: P&L Categories.
    Hierarchical structure for Profit & Loss categories.
    """
    __tablename__ = "dim_categories"

    # Business Key
    category_code = Column(String(255), unique=True, nullable=False, index=True, comment="Código da categoria")

    # Category Hierarchy
    level = Column(Integer, comment="Nível hierárquico (0=root, 1=level1, etc)")
    level_1 = Column(String(100), comment="P&L Level 1")
    level_2 = Column(String(100), comment="P&L Level 2")
    level_3 = Column(String(100), comment="P&L Level 3")

    # Multilingual Names
    name_pt = Column(String(255), comment="Nome em Português")
    name_en = Column(String(255), comment="Nome em Inglês")
    description = Column(Text, comment="Descrição da categoria")

    # Category Type
    category_type = Column(String(50), comment="Tipo: Receita, Despesa, etc")
    parent_code = Column(String(50), comment="Código da categoria pai")

    # Metadata
    is_active = Column(Boolean, default=True)
    extra_data = Column(JSON)

    # Relationships
    transactions = relationship("FactFinancialTransaction", back_populates="category")

    __table_args__ = (
        Index('idx_category_level', 'level'),
        Index('idx_category_type', 'category_type'),
        Index('idx_category_parent', 'parent_code'),
    )


class DimCostCenter(Base, BaseModelMixin):
    """
    Dimension: Cost Centers.
    Extended from existing cost_centers with OMIE integration.
    """
    __tablename__ = "dim_cost_centers"

    # Business Keys
    omie_cc_id = Column(BigInteger, unique=True, index=True, comment="ID do centro de custo no OMIE")
    cc_code = Column(String(50), unique=True, nullable=False, index=True, comment="Código do centro de custo")

    # Cost Center Attributes
    name = Column(String(255), nullable=False, comment="Nome do centro de custo")
    description = Column(Text, comment="Descrição")
    department_id = Column(UUID(as_uuid=True), ForeignKey("dim_departments.id"), comment="Departamento")

    # Hierarchy
    parent_cc_code = Column(String(50), comment="Código do CC pai")
    level = Column(Integer, default=1, comment="Nível hierárquico")

    # Distribution
    distribution_type = Column(String(20), comment="Tipo de rateio: fixo, percentual")
    distribution_value = Column(DECIMAL(15, 2), comment="Valor ou percentual de rateio")

    # Metadata
    is_active = Column(Boolean, default=True)
    extra_data = Column(JSON)

    # Relationships
    department = relationship("DimDepartment", back_populates="cost_centers")
    transactions = relationship("FactFinancialTransaction", back_populates="cost_center")

    __table_args__ = (
        Index('idx_cc_code', 'cc_code'),
        Index('idx_cc_department', 'department_id'),
    )


class DimDepartment(Base, BaseModelMixin):
    """
    Dimension: Departments.
    Extended from existing departments with OMIE integration.
    """
    __tablename__ = "dim_departments"

    # Business Keys
    omie_dept_code = Column(String(50), unique=True, index=True, comment="Código do departamento no OMIE")
    name = Column(String(255), nullable=False, comment="Nome do departamento")
    description = Column(Text, comment="Descrição do departamento")

    # Hierarchy
    parent_dept_code = Column(String(50), comment="Código do departamento pai")
    level = Column(Integer, default=1)

    # Metadata
    is_active = Column(Boolean, default=True)
    extra_data = Column(JSON)

    # Relationships
    cost_centers = relationship("DimCostCenter", back_populates="department")
    transactions = relationship("FactFinancialTransaction", back_populates="department")

    __table_args__ = (
        Index('idx_dept_code', 'omie_dept_code'),
    )


class DimDate(Base, BaseModelMixin):
    """
    Dimension: Date dimension for time-based analysis.
    Pre-populated with dates for analysis.
    """
    __tablename__ = "dim_dates"

    # Primary Date
    date_value = Column(Date, unique=True, nullable=False, index=True, comment="Data")

    # Date Attributes
    year = Column(Integer, nullable=False, index=True)
    quarter = Column(Integer, nullable=False, comment="Trimestre (1-4)")
    month = Column(Integer, nullable=False, index=True, comment="Mês (1-12)")
    month_name = Column(String(20), comment="Nome do mês")
    week = Column(Integer, comment="Semana do ano")
    day = Column(Integer, nullable=False, comment="Dia do mês")
    day_of_week = Column(Integer, comment="Dia da semana (1=Segunda)")
    day_name = Column(String(20), comment="Nome do dia")

    # Business Attributes
    is_weekend = Column(Boolean, default=False)
    is_holiday = Column(Boolean, default=False)
    fiscal_year = Column(Integer, comment="Ano fiscal")
    fiscal_quarter = Column(Integer, comment="Trimestre fiscal")
    fiscal_period = Column(String(20), comment="Período fiscal (YYYY-MM)")

    # Derived Attributes
    year_month = Column(String(7), index=True, comment="YYYY-MM")
    year_quarter = Column(String(7), comment="YYYY-Q1")

    __table_args__ = (
        Index('idx_date_year_month', 'year', 'month'),
        Index('idx_date_quarter', 'year', 'quarter'),
    )


# ============================================================================
# FACT TABLE
# ============================================================================

class FactFinancialTransaction(Base, BaseModelMixin):
    """
    Fact Table: Financial Transactions from OMIE.
    Contains all financial transactions (payables and receivables) with measures and foreign keys to dimensions.
    """
    __tablename__ = "fact_financial_transactions"

    # Foreign Keys to Dimensions
    client_id = Column(UUID(as_uuid=True), ForeignKey("dim_clients.id"), nullable=True, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("dim_categories.id"), nullable=True, index=True)
    cost_center_id = Column(UUID(as_uuid=True), ForeignKey("dim_cost_centers.id"), nullable=True, index=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("dim_departments.id"), nullable=True, index=True)

    # Date Foreign Keys
    issue_date_id = Column(UUID(as_uuid=True), ForeignKey("dim_dates.id"), nullable=True, index=True, comment="Data de emissão")
    due_date_id = Column(UUID(as_uuid=True), ForeignKey("dim_dates.id"), nullable=True, index=True, comment="Data de vencimento")
    payment_date_id = Column(UUID(as_uuid=True), ForeignKey("dim_dates.id"), nullable=True, index=True, comment="Data de pagamento")
    registration_date_id = Column(UUID(as_uuid=True), ForeignKey("dim_dates.id"), nullable=True, index=True, comment="Data de registro")

    # Business Keys (from OMIE)
    omie_title_id = Column(BigInteger, unique=True, nullable=False, index=True, comment="nCodTitulo - ID do título no OMIE")
    omie_internal_code = Column(String(50), index=True, comment="cCodIntTitulo - Código interno")

    # Transaction Identifiers
    title_number = Column(String(100), index=True, comment="cNumTitulo - Número do título")
    parcel_number = Column(String(20), comment="cNumParcela - Número da parcela")
    fiscal_document_number = Column(String(100), comment="cNumDocFiscal - Número do doc fiscal")

    # Transaction Classification
    transaction_type = Column(String(50), index=True, comment="cTipo - Tipo: NFS, Boleto, etc")
    nature = Column(String(50), comment="cNatureza - Natureza da operação")
    origin = Column(String(50), comment="cOrigem - Origem do título")
    status = Column(String(50), index=True, comment="cStatus - Status: RECEBIDO, PAGO, ABERTO")
    is_settled = Column(Boolean, index=True, comment="cLiquidado - Título liquidado")
    paid_or_received = Column(String(50), comment="Indicador de pago/recebido")

    # ===== MEASURES (Additive) =====

    # Main Values
    title_value = Column(DECIMAL(18, 2), nullable=False, index=True, comment="nValorTitulo - Valor principal")
    net_value = Column(DECIMAL(18, 2), comment="nValLiquido - Valor líquido")
    paid_value = Column(DECIMAL(18, 2), comment="nValPago - Valor pago")
    open_value = Column(DECIMAL(18, 2), comment="nValAberto - Valor em aberto")

    # Adjustments
    discount = Column(DECIMAL(18, 2), default=0, comment="nDesconto - Descontos")
    interest = Column(DECIMAL(18, 2), default=0, comment="nJuros - Juros")
    penalty = Column(DECIMAL(18, 2), default=0, comment="nMulta - Multas")

    # Taxes (Withholding)
    tax_cofins = Column(DECIMAL(18, 2), default=0, comment="nValorCOFINS - COFINS retido")
    tax_csll = Column(DECIMAL(18, 2), default=0, comment="nValorCSLL - CSLL retido")
    tax_inss = Column(DECIMAL(18, 2), default=0, comment="nValorINSS - INSS retido")
    tax_ir = Column(DECIMAL(18, 2), default=0, comment="nValorIR - IR retido")
    tax_iss = Column(DECIMAL(18, 2), default=0, comment="nValorISS - ISS retido")
    tax_pis = Column(DECIMAL(18, 2), default=0, comment="nValorPIS - PIS retido")
    total_taxes_withheld = Column(DECIMAL(18, 2), default=0, comment="Total de impostos retidos")

    # Tax Retention Flags
    has_cofins_retention = Column(Boolean, default=False, comment="cRetCOFINS")
    has_csll_retention = Column(Boolean, default=False, comment="cRetCSLL")
    has_inss_retention = Column(Boolean, default=False, comment="cRetINSS")
    has_ir_retention = Column(Boolean, default=False, comment="cRetIR")
    has_iss_retention = Column(Boolean, default=False, comment="cRetISS")
    has_pis_retention = Column(Boolean, default=False, comment="cRetPIS")

    # Linked Documents
    contract_number = Column(String(100), comment="cNumCtr - Número do contrato")
    omie_contract_id = Column(BigInteger, comment="nCodCtr - ID do contrato")
    service_order_number = Column(String(100), comment="cNumOS - Número da OS")
    omie_service_order_id = Column(BigInteger, comment="nCodOS - ID da OS")
    omie_invoice_id = Column(BigInteger, comment="nCodNF - ID da nota fiscal")
    operation = Column(String(50), comment="cOperacao - Tipo de operação")

    # Cost Allocation (if distributed across multiple CCs)
    distribution_percentage = Column(DECIMAL(5, 2), comment="nDistrPercentual - % de rateio")
    distribution_value = Column(DECIMAL(18, 2), comment="nDistrValor - Valor do rateio")
    fixed_value = Column(DECIMAL(18, 2), comment="nValorFixo - Valor fixo")

    # Observations
    observation = Column(Text, comment="observacao - Observações")
    description = Column(Text, comment="descricao - Descrição")

    # Payment Details (from lancamentos)
    payment_internal_code = Column(String(50), comment="cCodIntLanc - Código interno do lançamento")
    payment_nature = Column(String(50), comment="cNatureza do lançamento")
    payment_observation = Column(Text, comment="cObsLanc - Observação do lançamento")
    payment_value = Column(DECIMAL(18, 2), comment="nValLanc - Valor do lançamento")
    payment_discount = Column(DECIMAL(18, 2), comment="nDesconto do lançamento")
    payment_interest = Column(DECIMAL(18, 2), comment="nJuros do lançamento")
    payment_penalty = Column(DECIMAL(18, 2), comment="nMulta do lançamento")
    omie_payment_id = Column(BigInteger, comment="nCodLanc - ID do lançamento")
    omie_payment_cc_id = Column(BigInteger, comment="nIdLancCC - ID do lançamento CC")

    # Metadata
    source_system = Column(String(50), default="OMIE", comment="Sistema de origem")
    source_row_index = Column(Integer, comment="Índice da linha no Excel")
    extra_data = Column(JSON, comment="Dados adicionais não estruturados")

    # Relationships
    client = relationship("DimClient", back_populates="transactions")
    category = relationship("DimCategory", back_populates="transactions")
    cost_center = relationship("DimCostCenter", back_populates="transactions")
    department = relationship("DimDepartment", back_populates="transactions")

    # Indexes for common queries
    __table_args__ = (
        Index('idx_fact_client_date', 'client_id', 'due_date_id'),
        Index('idx_fact_category_date', 'category_id', 'due_date_id'),
        Index('idx_fact_status_type', 'status', 'transaction_type'),
        Index('idx_fact_value', 'title_value'),
        Index('idx_fact_omie_title', 'omie_title_id'),
        Index('idx_fact_dates', 'issue_date_id', 'due_date_id', 'payment_date_id'),
    )
