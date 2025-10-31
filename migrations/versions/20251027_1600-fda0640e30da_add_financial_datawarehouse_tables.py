"""add_financial_datawarehouse_tables

Revision ID: fda0640e30da
Revises: 007_add_employee_name
Create Date: 2025-10-27 16:00:52.175027

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "fda0640e30da"
down_revision = "007_add_employee_name"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create dim_clients table
    op.create_table(
        "dim_clients",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column(
            "omie_client_id",
            sa.Integer(),
            nullable=False,
            comment="ID do cliente no OMIE",
        ),
        sa.Column("tax_id", sa.String(length=18), nullable=True, comment="CPF/CNPJ do cliente"),
        sa.Column("legal_name", sa.String(length=255), nullable=True, comment="Razão social"),
        sa.Column("trade_name", sa.String(length=255), nullable=True, comment="Nome fantasia"),
        sa.Column(
            "key_account", sa.String(length=100), nullable=True, comment="Key Account classification"
        ),
        sa.Column("vertical", sa.String(length=100), nullable=True, comment="Vertical/Segmento"),
        sa.Column("pd7_id", sa.String(length=50), nullable=True, comment="ID interno PD7"),
        sa.Column("geo", sa.String(length=100), nullable=True, comment="Geografia/Região"),
        sa.Column("state", sa.String(length=2), nullable=True, comment="Estado (UF)"),
        sa.Column("source_system", sa.String(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True, comment="Dados adicionais do cliente"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("omie_client_id"),
    )
    op.create_index("idx_client_tax_id", "dim_clients", ["tax_id"], unique=False)
    op.create_index("idx_client_trade_name", "dim_clients", ["trade_name"], unique=False)
    op.create_index("idx_client_vertical", "dim_clients", ["vertical"], unique=False)
    op.create_index(op.f("ix_dim_clients_omie_client_id"), "dim_clients", ["omie_client_id"], unique=False)
    op.create_index(op.f("ix_dim_clients_tax_id"), "dim_clients", ["tax_id"], unique=False)
    op.create_index(op.f("ix_dim_clients_trade_name"), "dim_clients", ["trade_name"], unique=False)

    # Create dim_categories table
    op.create_table(
        "dim_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column(
            "category_code",
            sa.String(length=50),
            nullable=False,
            comment="Código da categoria",
        ),
        sa.Column("level", sa.Integer(), nullable=True, comment="Nível hierárquico (0=root, 1=level1, etc)"),
        sa.Column("level_1", sa.String(length=100), nullable=True, comment="P&L Level 1"),
        sa.Column("level_2", sa.String(length=100), nullable=True, comment="P&L Level 2"),
        sa.Column("level_3", sa.String(length=100), nullable=True, comment="P&L Level 3"),
        sa.Column("name_pt", sa.String(length=255), nullable=True, comment="Nome em Português"),
        sa.Column("name_en", sa.String(length=255), nullable=True, comment="Nome em Inglês"),
        sa.Column("description", sa.Text(), nullable=True, comment="Descrição da categoria"),
        sa.Column("category_type", sa.String(length=50), nullable=True, comment="Tipo: Receita, Despesa, etc"),
        sa.Column("parent_code", sa.String(length=50), nullable=True, comment="Código da categoria pai"),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category_code"),
    )
    op.create_index("idx_category_level", "dim_categories", ["level"], unique=False)
    op.create_index("idx_category_parent", "dim_categories", ["parent_code"], unique=False)
    op.create_index("idx_category_type", "dim_categories", ["category_type"], unique=False)
    op.create_index(op.f("ix_dim_categories_category_code"), "dim_categories", ["category_code"], unique=False)

    # Create dim_departments table
    op.create_table(
        "dim_departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column(
            "omie_dept_code",
            sa.String(length=50),
            nullable=True,
            comment="Código do departamento no OMIE",
        ),
        sa.Column("name", sa.String(length=255), nullable=False, comment="Nome do departamento"),
        sa.Column("description", sa.Text(), nullable=True, comment="Descrição do departamento"),
        sa.Column("parent_dept_code", sa.String(length=50), nullable=True, comment="Código do departamento pai"),
        sa.Column("level", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("omie_dept_code"),
    )
    op.create_index("idx_dept_code", "dim_departments", ["omie_dept_code"], unique=False)
    op.create_index(op.f("ix_dim_departments_omie_dept_code"), "dim_departments", ["omie_dept_code"], unique=False)

    # Create dim_dates table
    op.create_table(
        "dim_dates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("date_value", sa.Date(), nullable=False, comment="Data"),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("quarter", sa.Integer(), nullable=False, comment="Trimestre (1-4)"),
        sa.Column("month", sa.Integer(), nullable=False, comment="Mês (1-12)"),
        sa.Column("month_name", sa.String(length=20), nullable=True, comment="Nome do mês"),
        sa.Column("week", sa.Integer(), nullable=True, comment="Semana do ano"),
        sa.Column("day", sa.Integer(), nullable=False, comment="Dia do mês"),
        sa.Column("day_of_week", sa.Integer(), nullable=True, comment="Dia da semana (1=Segunda)"),
        sa.Column("day_name", sa.String(length=20), nullable=True, comment="Nome do dia"),
        sa.Column("is_weekend", sa.Boolean(), nullable=True),
        sa.Column("is_holiday", sa.Boolean(), nullable=True),
        sa.Column("fiscal_year", sa.Integer(), nullable=True, comment="Ano fiscal"),
        sa.Column("fiscal_quarter", sa.Integer(), nullable=True, comment="Trimestre fiscal"),
        sa.Column("fiscal_period", sa.String(length=20), nullable=True, comment="Período fiscal (YYYY-MM)"),
        sa.Column("year_month", sa.String(length=7), nullable=True, comment="YYYY-MM"),
        sa.Column("year_quarter", sa.String(length=7), nullable=True, comment="YYYY-Q1"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date_value"),
    )
    op.create_index("idx_date_quarter", "dim_dates", ["year", "quarter"], unique=False)
    op.create_index("idx_date_year_month", "dim_dates", ["year", "month"], unique=False)
    op.create_index(op.f("ix_dim_dates_date_value"), "dim_dates", ["date_value"], unique=False)
    op.create_index(op.f("ix_dim_dates_month"), "dim_dates", ["month"], unique=False)
    op.create_index(op.f("ix_dim_dates_year"), "dim_dates", ["year"], unique=False)
    op.create_index(op.f("ix_dim_dates_year_month"), "dim_dates", ["year_month"], unique=False)

    # Create dim_cost_centers table
    op.create_table(
        "dim_cost_centers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("omie_cc_id", sa.Integer(), nullable=True, comment="ID do centro de custo no OMIE"),
        sa.Column("cc_code", sa.String(length=50), nullable=False, comment="Código do centro de custo"),
        sa.Column("name", sa.String(length=255), nullable=False, comment="Nome do centro de custo"),
        sa.Column("description", sa.Text(), nullable=True, comment="Descrição"),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True, comment="Departamento"),
        sa.Column("parent_cc_code", sa.String(length=50), nullable=True, comment="Código do CC pai"),
        sa.Column("level", sa.Integer(), nullable=True, comment="Nível hierárquico"),
        sa.Column("distribution_type", sa.String(length=20), nullable=True, comment="Tipo de rateio: fixo, percentual"),
        sa.Column("distribution_value", sa.DECIMAL(precision=15, scale=2), nullable=True, comment="Valor ou percentual de rateio"),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["department_id"],
            ["dim_departments.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cc_code"),
        sa.UniqueConstraint("omie_cc_id"),
    )
    op.create_index("idx_cc_code", "dim_cost_centers", ["cc_code"], unique=False)
    op.create_index("idx_cc_department", "dim_cost_centers", ["department_id"], unique=False)
    op.create_index(op.f("ix_dim_cost_centers_cc_code"), "dim_cost_centers", ["cc_code"], unique=False)
    op.create_index(op.f("ix_dim_cost_centers_omie_cc_id"), "dim_cost_centers", ["omie_cc_id"], unique=False)

    # Create fact_financial_transactions table
    op.create_table(
        "fact_financial_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cost_center_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("issue_date_id", postgresql.UUID(as_uuid=True), nullable=True, comment="Data de emissão"),
        sa.Column("due_date_id", postgresql.UUID(as_uuid=True), nullable=True, comment="Data de vencimento"),
        sa.Column("payment_date_id", postgresql.UUID(as_uuid=True), nullable=True, comment="Data de pagamento"),
        sa.Column("registration_date_id", postgresql.UUID(as_uuid=True), nullable=True, comment="Data de registro"),
        sa.Column("omie_title_id", sa.Integer(), nullable=False, comment="nCodTitulo - ID do título no OMIE"),
        sa.Column("omie_internal_code", sa.String(length=50), nullable=True, comment="cCodIntTitulo - Código interno"),
        sa.Column("title_number", sa.String(length=100), nullable=True, comment="cNumTitulo - Número do título"),
        sa.Column("parcel_number", sa.String(length=20), nullable=True, comment="cNumParcela - Número da parcela"),
        sa.Column("fiscal_document_number", sa.String(length=100), nullable=True, comment="cNumDocFiscal - Número do doc fiscal"),
        sa.Column("transaction_type", sa.String(length=50), nullable=True, comment="cTipo - Tipo: NFS, Boleto, etc"),
        sa.Column("nature", sa.String(length=50), nullable=True, comment="cNatureza - Natureza da operação"),
        sa.Column("origin", sa.String(length=50), nullable=True, comment="cOrigem - Origem do título"),
        sa.Column("status", sa.String(length=50), nullable=True, comment="cStatus - Status: RECEBIDO, PAGO, ABERTO"),
        sa.Column("is_settled", sa.Boolean(), nullable=True, comment="cLiquidado - Título liquidado"),
        sa.Column("paid_or_received", sa.String(length=50), nullable=True, comment="Indicador de pago/recebido"),
        sa.Column("title_value", sa.DECIMAL(precision=18, scale=2), nullable=False, comment="nValorTitulo - Valor principal"),
        sa.Column("net_value", sa.DECIMAL(precision=18, scale=2), nullable=True, comment="nValLiquido - Valor líquido"),
        sa.Column("paid_value", sa.DECIMAL(precision=18, scale=2), nullable=True, comment="nValPago - Valor pago"),
        sa.Column("open_value", sa.DECIMAL(precision=18, scale=2), nullable=True, comment="nValAberto - Valor em aberto"),
        sa.Column("discount", sa.DECIMAL(precision=18, scale=2), nullable=True, comment="nDesconto - Descontos"),
        sa.Column("interest", sa.DECIMAL(precision=18, scale=2), nullable=True, comment="nJuros - Juros"),
        sa.Column("penalty", sa.DECIMAL(precision=18, scale=2), nullable=True, comment="nMulta - Multas"),
        sa.Column("tax_cofins", sa.DECIMAL(precision=18, scale=2), nullable=True, comment="nValorCOFINS - COFINS retido"),
        sa.Column("tax_csll", sa.DECIMAL(precision=18, scale=2), nullable=True, comment="nValorCSLL - CSLL retido"),
        sa.Column("tax_inss", sa.DECIMAL(precision=18, scale=2), nullable=True, comment="nValorINSS - INSS retido"),
        sa.Column("tax_ir", sa.DECIMAL(precision=18, scale=2), nullable=True, comment="nValorIR - IR retido"),
        sa.Column("tax_iss", sa.DECIMAL(precision=18, scale=2), nullable=True, comment="nValorISS - ISS retido"),
        sa.Column("tax_pis", sa.DECIMAL(precision=18, scale=2), nullable=True, comment="nValorPIS - PIS retido"),
        sa.Column("total_taxes_withheld", sa.DECIMAL(precision=18, scale=2), nullable=True, comment="Total de impostos retidos"),
        sa.Column("has_cofins_retention", sa.Boolean(), nullable=True, comment="cRetCOFINS"),
        sa.Column("has_csll_retention", sa.Boolean(), nullable=True, comment="cRetCSLL"),
        sa.Column("has_inss_retention", sa.Boolean(), nullable=True, comment="cRetINSS"),
        sa.Column("has_ir_retention", sa.Boolean(), nullable=True, comment="cRetIR"),
        sa.Column("has_iss_retention", sa.Boolean(), nullable=True, comment="cRetISS"),
        sa.Column("has_pis_retention", sa.Boolean(), nullable=True, comment="cRetPIS"),
        sa.Column("contract_number", sa.String(length=100), nullable=True, comment="cNumCtr - Número do contrato"),
        sa.Column("omie_contract_id", sa.Integer(), nullable=True, comment="nCodCtr - ID do contrato"),
        sa.Column("service_order_number", sa.String(length=100), nullable=True, comment="cNumOS - Número da OS"),
        sa.Column("omie_service_order_id", sa.Integer(), nullable=True, comment="nCodOS - ID da OS"),
        sa.Column("omie_invoice_id", sa.Integer(), nullable=True, comment="nCodNF - ID da nota fiscal"),
        sa.Column("operation", sa.String(length=50), nullable=True, comment="cOperacao - Tipo de operação"),
        sa.Column("distribution_percentage", sa.DECIMAL(precision=5, scale=2), nullable=True, comment="nDistrPercentual - % de rateio"),
        sa.Column("distribution_value", sa.DECIMAL(precision=18, scale=2), nullable=True, comment="nDistrValor - Valor do rateio"),
        sa.Column("fixed_value", sa.DECIMAL(precision=18, scale=2), nullable=True, comment="nValorFixo - Valor fixo"),
        sa.Column("observation", sa.Text(), nullable=True, comment="observacao - Observações"),
        sa.Column("description", sa.Text(), nullable=True, comment="descricao - Descrição"),
        sa.Column("payment_internal_code", sa.String(length=50), nullable=True, comment="cCodIntLanc - Código interno do lançamento"),
        sa.Column("payment_nature", sa.String(length=50), nullable=True, comment="cNatureza do lançamento"),
        sa.Column("payment_observation", sa.Text(), nullable=True, comment="cObsLanc - Observação do lançamento"),
        sa.Column("payment_value", sa.DECIMAL(precision=18, scale=2), nullable=True, comment="nValLanc - Valor do lançamento"),
        sa.Column("payment_discount", sa.DECIMAL(precision=18, scale=2), nullable=True, comment="nDesconto do lançamento"),
        sa.Column("payment_interest", sa.DECIMAL(precision=18, scale=2), nullable=True, comment="nJuros do lançamento"),
        sa.Column("payment_penalty", sa.DECIMAL(precision=18, scale=2), nullable=True, comment="nMulta do lançamento"),
        sa.Column("omie_payment_id", sa.Integer(), nullable=True, comment="nCodLanc - ID do lançamento"),
        sa.Column("omie_payment_cc_id", sa.Integer(), nullable=True, comment="nIdLancCC - ID do lançamento CC"),
        sa.Column("source_system", sa.String(length=50), nullable=True, comment="Sistema de origem"),
        sa.Column("source_row_index", sa.Integer(), nullable=True, comment="Índice da linha no Excel"),
        sa.Column("extra_data", sa.JSON(), nullable=True, comment="Dados adicionais não estruturados"),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["dim_categories.id"],
        ),
        sa.ForeignKeyConstraint(
            ["client_id"],
            ["dim_clients.id"],
        ),
        sa.ForeignKeyConstraint(
            ["cost_center_id"],
            ["dim_cost_centers.id"],
        ),
        sa.ForeignKeyConstraint(
            ["department_id"],
            ["dim_departments.id"],
        ),
        sa.ForeignKeyConstraint(
            ["due_date_id"],
            ["dim_dates.id"],
        ),
        sa.ForeignKeyConstraint(
            ["issue_date_id"],
            ["dim_dates.id"],
        ),
        sa.ForeignKeyConstraint(
            ["payment_date_id"],
            ["dim_dates.id"],
        ),
        sa.ForeignKeyConstraint(
            ["registration_date_id"],
            ["dim_dates.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("omie_title_id"),
    )
    op.create_index("idx_fact_category_date", "fact_financial_transactions", ["category_id", "due_date_id"], unique=False)
    op.create_index("idx_fact_client_date", "fact_financial_transactions", ["client_id", "due_date_id"], unique=False)
    op.create_index("idx_fact_dates", "fact_financial_transactions", ["issue_date_id", "due_date_id", "payment_date_id"], unique=False)
    op.create_index("idx_fact_omie_title", "fact_financial_transactions", ["omie_title_id"], unique=False)
    op.create_index("idx_fact_status_type", "fact_financial_transactions", ["status", "transaction_type"], unique=False)
    op.create_index("idx_fact_value", "fact_financial_transactions", ["title_value"], unique=False)
    op.create_index(op.f("ix_fact_financial_transactions_category_id"), "fact_financial_transactions", ["category_id"], unique=False)
    op.create_index(op.f("ix_fact_financial_transactions_client_id"), "fact_financial_transactions", ["client_id"], unique=False)
    op.create_index(op.f("ix_fact_financial_transactions_cost_center_id"), "fact_financial_transactions", ["cost_center_id"], unique=False)
    op.create_index(op.f("ix_fact_financial_transactions_department_id"), "fact_financial_transactions", ["department_id"], unique=False)
    op.create_index(op.f("ix_fact_financial_transactions_due_date_id"), "fact_financial_transactions", ["due_date_id"], unique=False)
    op.create_index(op.f("ix_fact_financial_transactions_is_settled"), "fact_financial_transactions", ["is_settled"], unique=False)
    op.create_index(op.f("ix_fact_financial_transactions_issue_date_id"), "fact_financial_transactions", ["issue_date_id"], unique=False)
    op.create_index(op.f("ix_fact_financial_transactions_omie_internal_code"), "fact_financial_transactions", ["omie_internal_code"], unique=False)
    op.create_index(op.f("ix_fact_financial_transactions_omie_title_id"), "fact_financial_transactions", ["omie_title_id"], unique=False)
    op.create_index(op.f("ix_fact_financial_transactions_payment_date_id"), "fact_financial_transactions", ["payment_date_id"], unique=False)
    op.create_index(op.f("ix_fact_financial_transactions_registration_date_id"), "fact_financial_transactions", ["registration_date_id"], unique=False)
    op.create_index(op.f("ix_fact_financial_transactions_status"), "fact_financial_transactions", ["status"], unique=False)
    op.create_index(op.f("ix_fact_financial_transactions_title_number"), "fact_financial_transactions", ["title_number"], unique=False)
    op.create_index(op.f("ix_fact_financial_transactions_title_value"), "fact_financial_transactions", ["title_value"], unique=False)
    op.create_index(op.f("ix_fact_financial_transactions_transaction_type"), "fact_financial_transactions", ["transaction_type"], unique=False)


def downgrade() -> None:
    # Drop fact table first
    op.drop_index(op.f("ix_fact_financial_transactions_transaction_type"), table_name="fact_financial_transactions")
    op.drop_index(op.f("ix_fact_financial_transactions_title_value"), table_name="fact_financial_transactions")
    op.drop_index(op.f("ix_fact_financial_transactions_title_number"), table_name="fact_financial_transactions")
    op.drop_index(op.f("ix_fact_financial_transactions_status"), table_name="fact_financial_transactions")
    op.drop_index(op.f("ix_fact_financial_transactions_registration_date_id"), table_name="fact_financial_transactions")
    op.drop_index(op.f("ix_fact_financial_transactions_payment_date_id"), table_name="fact_financial_transactions")
    op.drop_index(op.f("ix_fact_financial_transactions_omie_title_id"), table_name="fact_financial_transactions")
    op.drop_index(op.f("ix_fact_financial_transactions_omie_internal_code"), table_name="fact_financial_transactions")
    op.drop_index(op.f("ix_fact_financial_transactions_issue_date_id"), table_name="fact_financial_transactions")
    op.drop_index(op.f("ix_fact_financial_transactions_is_settled"), table_name="fact_financial_transactions")
    op.drop_index(op.f("ix_fact_financial_transactions_due_date_id"), table_name="fact_financial_transactions")
    op.drop_index(op.f("ix_fact_financial_transactions_department_id"), table_name="fact_financial_transactions")
    op.drop_index(op.f("ix_fact_financial_transactions_cost_center_id"), table_name="fact_financial_transactions")
    op.drop_index(op.f("ix_fact_financial_transactions_client_id"), table_name="fact_financial_transactions")
    op.drop_index(op.f("ix_fact_financial_transactions_category_id"), table_name="fact_financial_transactions")
    op.drop_index("idx_fact_value", table_name="fact_financial_transactions")
    op.drop_index("idx_fact_status_type", table_name="fact_financial_transactions")
    op.drop_index("idx_fact_omie_title", table_name="fact_financial_transactions")
    op.drop_index("idx_fact_dates", table_name="fact_financial_transactions")
    op.drop_index("idx_fact_client_date", table_name="fact_financial_transactions")
    op.drop_index("idx_fact_category_date", table_name="fact_financial_transactions")
    op.drop_table("fact_financial_transactions")

    # Drop dimension tables
    op.drop_index(op.f("ix_dim_cost_centers_omie_cc_id"), table_name="dim_cost_centers")
    op.drop_index(op.f("ix_dim_cost_centers_cc_code"), table_name="dim_cost_centers")
    op.drop_index("idx_cc_department", table_name="dim_cost_centers")
    op.drop_index("idx_cc_code", table_name="dim_cost_centers")
    op.drop_table("dim_cost_centers")

    op.drop_index(op.f("ix_dim_dates_year_month"), table_name="dim_dates")
    op.drop_index(op.f("ix_dim_dates_year"), table_name="dim_dates")
    op.drop_index(op.f("ix_dim_dates_month"), table_name="dim_dates")
    op.drop_index(op.f("ix_dim_dates_date_value"), table_name="dim_dates")
    op.drop_index("idx_date_year_month", table_name="dim_dates")
    op.drop_index("idx_date_quarter", table_name="dim_dates")
    op.drop_table("dim_dates")

    op.drop_index(op.f("ix_dim_departments_omie_dept_code"), table_name="dim_departments")
    op.drop_index("idx_dept_code", table_name="dim_departments")
    op.drop_table("dim_departments")

    op.drop_index(op.f("ix_dim_categories_category_code"), table_name="dim_categories")
    op.drop_index("idx_category_type", table_name="dim_categories")
    op.drop_index("idx_category_parent", table_name="dim_categories")
    op.drop_index("idx_category_level", table_name="dim_categories")
    op.drop_table("dim_categories")

    op.drop_index(op.f("ix_dim_clients_trade_name"), table_name="dim_clients")
    op.drop_index(op.f("ix_dim_clients_tax_id"), table_name="dim_clients")
    op.drop_index(op.f("ix_dim_clients_omie_client_id"), table_name="dim_clients")
    op.drop_index("idx_client_vertical", table_name="dim_clients")
    op.drop_index("idx_client_trade_name", table_name="dim_clients")
    op.drop_index("idx_client_tax_id", table_name="dim_clients")
    op.drop_table("dim_clients")
