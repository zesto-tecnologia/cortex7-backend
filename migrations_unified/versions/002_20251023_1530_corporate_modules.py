"""Corporate modules: financial, HR, legal, procurement

Revision ID: 002_corporate_modules
Revises: 001_unified_foundation
Create Date: 2025-10-23 15:30:00.000000

This migration adds all corporate module tables:
- Documents (with vector embeddings for semantic search)
- Financial module (cost centers, suppliers, accounts payable)
- Corporate cards module (cards, invoices, transactions)
- Procurement module (purchase orders)
- HR module (employees, employment contracts)
- Legal module (contracts, legal processes)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_corporate_modules'
down_revision = '001_unified_foundation'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # DOCUMENTOS (with vector embeddings)
    # ============================================
    op.create_table('documents',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('department', sa.String(length=50), nullable=False, comment='legal, financial, hr, procurement'),
        sa.Column('type', sa.String(length=50), nullable=False, comment='contract, invoice, resume, policy'),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('original_content', sa.Text(), nullable=True, comment='Text extracted by extractor'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='Structured data extracted'),
        sa.Column('file_url', sa.String(length=500), nullable=True, comment='S3/Storage link'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Documents with embeddings for semantic search'
    )

    # Add vector column using raw SQL (pgvector extension)
    op.execute('ALTER TABLE documents ADD COLUMN embedding vector(1536)')

    # Create vector index for semantic search
    op.execute("""
        CREATE INDEX idx_docs_embedding ON documents
        USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
    """)

    # Create other indexes
    op.create_index('idx_docs_empresa_dept', 'documents', ['company_id', 'department'], unique=False)
    op.create_index('idx_docs_tipo', 'documents', ['type'], unique=False)
    op.create_index('idx_docs_status', 'documents', ['status'], unique=False)
    op.execute('CREATE INDEX idx_docs_metadata ON documents USING gin(metadata)')

    # ============================================
    # FINANCIAL MODULE
    # ============================================

    # Cost Centers
    op.create_table('cost_centers',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('department', sa.String(length=50), nullable=True),
        sa.Column('monthly_budget', sa.Numeric(15, 2), nullable=True),
        sa.Column('current_spending', sa.Numeric(15, 2), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        comment='Cost centers for budget control'
    )
    op.create_index('idx_cc_codigo', 'cost_centers', ['code'], unique=False)
    op.create_index('idx_cc_empresa', 'cost_centers', ['company_id'], unique=False)

    # Suppliers
    op.create_table('suppliers',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('tax_id', sa.String(length=14), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True, comment='IT, Cleaning, Materials'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('bank_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('contacts', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='[{name, email, phone}]'),
        sa.Column('ratings', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Performance history'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tax_id'),
        comment='Fornecedores cadastrados no sistema'
    )
    op.create_index('idx_forn_cnpj', 'suppliers', ['tax_id'], unique=False)
    op.create_index('idx_forn_empresa', 'suppliers', ['company_id'], unique=False)
    op.create_index('idx_forn_status', 'suppliers', ['status'], unique=False)

    # Accounts Payable
    op.create_table('accounts_payable',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('supplier_id', sa.Uuid(), nullable=True),
        sa.Column('document_id', sa.Uuid(), nullable=True),
        sa.Column('document_number', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pendente', comment='pendente, approved, pago, cancelado'),
        sa.Column('cost_center', sa.String(length=50), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True, comment='Materiais, Serviços, Pessoal'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='installment, forma_pagamento, etc'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='5', comment='1=crítico, 5=normal, 10=baixo'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='Contas a pagar do módulo financeiro'
    )
    op.create_index('idx_cp_vencimento', 'accounts_payable', ['due_date'], unique=False)
    op.create_index('idx_cp_status', 'accounts_payable', ['status'], unique=False)
    op.create_index('idx_cp_empresa', 'accounts_payable', ['company_id'], unique=False)
    op.create_index('idx_cp_fornecedor', 'accounts_payable', ['supplier_id'], unique=False)

    # ============================================
    # CARDS MODULE
    # ============================================

    # Corporate Cards
    op.create_table('corporate_cards',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('cardholder_id', sa.Uuid(), nullable=True),
        sa.Column('masked_number', sa.String(length=20), nullable=False, comment='**** **** **** 1234'),
        sa.Column('card_brand', sa.String(length=20), nullable=False, comment='Visa, Master, Amex'),
        sa.Column('type', sa.String(length=20), nullable=False, server_default='corporativo', comment='corporativo, empresarial'),
        sa.Column('credit_limit', sa.Numeric(15, 2), nullable=True),
        sa.Column('available_credit', sa.Numeric(15, 2), nullable=True),
        sa.Column('invoice_due_day', sa.Integer(), nullable=True, comment='Dia do mês (1-31)'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active', comment='active, bloqueado, cancelado'),
        sa.Column('default_cost_center', sa.String(length=50), nullable=True),
        sa.Column('department', sa.String(length=50), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Dados do banco, taxas, etc'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cardholder_id'], ['user_profiles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='Cartões de crédito corporativos'
    )
    op.create_index('idx_cartoes_portador', 'corporate_cards', ['cardholder_id'], unique=False)
    op.create_index('idx_cartoes_empresa', 'corporate_cards', ['company_id'], unique=False)
    op.create_index('idx_cartoes_status', 'corporate_cards', ['status'], unique=False)

    # Card Invoices
    op.create_table('card_invoices',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('card_id', sa.Uuid(), nullable=False),
        sa.Column('document_id', sa.Uuid(), nullable=True),
        sa.Column('reference', sa.String(length=7), nullable=False, comment='MM/YYYY (ex: 10/2025)'),
        sa.Column('closing_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('total_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('paid_amount', sa.Numeric(15, 2), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='aberta', comment='aberta, parcialmente_paga, paga, atrasada, contestada'),
        sa.Column('account_payable_id', sa.Uuid(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='IOF, juros, multas'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['card_id'], ['corporate_cards.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['account_payable_id'], ['accounts_payable.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('card_id', 'reference', name='uq_fatura_cartao_ref'),
        comment='Faturas mensais dos cartões corporativos'
    )
    op.create_index('idx_faturas_cartao', 'card_invoices', ['card_id'], unique=False)
    op.create_index('idx_faturas_vencimento', 'card_invoices', ['due_date'], unique=False)
    op.create_index('idx_faturas_status', 'card_invoices', ['status'], unique=False)
    op.create_index('idx_faturas_empresa', 'card_invoices', ['company_id'], unique=False)

    # Card Transactions
    op.create_table('card_transactions',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('invoice_id', sa.Uuid(), nullable=False),
        sa.Column('card_id', sa.Uuid(), nullable=False),
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('posting_date', sa.Date(), nullable=False, comment='Data que aparece na fatura'),
        sa.Column('merchant', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True, comment='Alimentacao, Transporte, Software, Hospedagem'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('usd_amount', sa.Numeric(15, 2), nullable=True, comment='If international transaction'),
        sa.Column('exchange_rate', sa.Numeric(10, 4), nullable=True, comment='Conversion rate'),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='BRL'),
        sa.Column('installment', sa.String(length=10), nullable=True, comment='"1/3", "2/3" se parcelado'),
        sa.Column('cost_center', sa.String(length=50), nullable=True),
        sa.Column('project', sa.String(length=100), nullable=True, comment='Se vinculado a project específico'),
        sa.Column('approved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('approver_id', sa.Uuid(), nullable=True),
        sa.Column('approved_at', sa.Date(), nullable=True),
        sa.Column('justification', sa.Text(), nullable=True, comment='Justificativa da despesa'),
        sa.Column('receipt_url', sa.String(length=500), nullable=True, comment='Link para recibo/nota fiscal'),
        sa.Column('disputed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('dispute_reason', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='milhas, cashback, etc'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invoice_id'], ['card_invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['card_id'], ['corporate_cards.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approver_id'], ['user_profiles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='Lançamentos individuais em cada fatura'
    )
    op.create_index('idx_lanc_fatura', 'card_transactions', ['invoice_id'], unique=False)
    op.create_index('idx_lanc_cartao', 'card_transactions', ['card_id'], unique=False)
    op.create_index('idx_lanc_data', 'card_transactions', ['transaction_date'], unique=False)
    op.create_index('idx_lanc_categoria', 'card_transactions', ['category'], unique=False)
    op.create_index('idx_lanc_empresa', 'card_transactions', ['company_id'], unique=False)
    op.execute('CREATE INDEX idx_lanc_aprovacao ON card_transactions(approved) WHERE NOT approved')

    # ============================================
    # PROCUREMENT MODULE
    # ============================================

    # Purchase Orders
    op.create_table('purchase_orders',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('number', sa.String(length=20), nullable=False),
        sa.Column('requester_id', sa.Uuid(), nullable=False),
        sa.Column('supplier_id', sa.Uuid(), nullable=False),
        sa.Column('total_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='rascunho', comment='rascunho, aguardando_aprovacao, aprovada, pedido_emitido, recebido, cancelada'),
        sa.Column('items', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='[{description, qtd, valor_unit}]'),
        sa.Column('approvers', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='[{user_profile_id, nivel, approved_at}]'),
        sa.Column('cost_center', sa.String(length=50), nullable=True),
        sa.Column('expected_delivery_date', sa.Date(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['requester_id'], ['user_profiles.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('number'),
        comment='Ordens de compra do módulo de suprimentos'
    )
    op.create_index('idx_oc_numero', 'purchase_orders', ['number'], unique=False)
    op.create_index('idx_oc_status', 'purchase_orders', ['status'], unique=False)
    op.create_index('idx_oc_empresa', 'purchase_orders', ['company_id'], unique=False)
    op.create_index('idx_oc_solicitante', 'purchase_orders', ['requester_id'], unique=False)
    op.create_index('idx_oc_fornecedor', 'purchase_orders', ['supplier_id'], unique=False)

    # ============================================
    # HR MODULE
    # ============================================

    # Employees
    op.create_table('employees',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('tax_id', sa.String(length=11), nullable=False),
        sa.Column('birth_date', sa.Date(), nullable=True),
        sa.Column('hire_date', sa.Date(), nullable=False),
        sa.Column('termination_date', sa.Date(), nullable=True),
        sa.Column('position', sa.String(length=100), nullable=False),
        sa.Column('department_id', sa.Uuid(), nullable=True),
        sa.Column('salary', sa.Numeric(10, 2), nullable=True),
        sa.Column('contract_type', sa.String(length=20), nullable=True, comment='CLT, PJ, Estagio'),
        sa.Column('work_mode', sa.String(length=20), nullable=True, comment='Presencial, Remoto, Hibrido'),
        sa.Column('personal_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Endereço, contacts emergência'),
        sa.Column('benefits', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='VT, VA, plano saúde'),
        sa.Column('documents', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Links docs: RG, CPF, carteira trabalho'),
        sa.Column('vacation', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='[{periodo_aquisitivo, dias_disponiveis, history}]'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user_profiles.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tax_id'),
        comment='Funcionários cadastrados no sistema de RH'
    )
    op.create_index('idx_func_cpf', 'employees', ['tax_id'], unique=False)
    op.create_index('idx_func_empresa', 'employees', ['company_id'], unique=False)
    op.create_index('idx_func_status', 'employees', ['status'], unique=False)
    op.create_index('idx_func_departamento', 'employees', ['department_id'], unique=False)
    op.create_index('idx_func_usuario', 'employees', ['user_id'], unique=False)

    # Employment Contracts
    op.create_table('employment_contracts',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('employee_id', sa.Uuid(), nullable=False),
        sa.Column('document_id', sa.Uuid(), nullable=True),
        sa.Column('contract_type', sa.String(length=20), nullable=False, comment='hire, amendment, termination'),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True, comment='Texto completo do contrato'),
        sa.Column('special_clauses', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('signed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('employee_signature_date', sa.Date(), nullable=True),
        sa.Column('company_signature_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='Contratos de trabalho de funcionários'
    )
    op.create_index('idx_ct_funcionario', 'employment_contracts', ['employee_id'], unique=False)
    op.create_index('idx_ct_tipo', 'employment_contracts', ['contract_type'], unique=False)
    op.create_index('idx_ct_documento', 'employment_contracts', ['document_id'], unique=False)

    # ============================================
    # LEGAL MODULE
    # ============================================

    # Contracts
    op.create_table('contracts',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('document_id', sa.Uuid(), nullable=True),
        sa.Column('contract_type', sa.String(length=50), nullable=False, comment='supplier, client, partnership, employment'),
        sa.Column('counterparty', sa.String(length=255), nullable=False),
        sa.Column('counterparty_tax_id', sa.String(length=14), nullable=True),
        sa.Column('subject', sa.Text(), nullable=False, comment='Descrição do contrato'),
        sa.Column('amount', sa.Numeric(15, 2), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('auto_renewal', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='vigente', comment='rascunho, aprovacao, vigente, rescindido, encerrado, vencido'),
        sa.Column('critical_clauses', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Multas, SLAs, confidencialidade'),
        sa.Column('important_dates', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='[{description, date, notified}]'),
        sa.Column('responsible_id', sa.Uuid(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['responsible_id'], ['user_profiles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='Contratos jurídicos gerais'
    )
    op.create_index('idx_contr_empresa', 'contracts', ['company_id'], unique=False)
    op.create_index('idx_contr_status', 'contracts', ['status'], unique=False)
    op.create_index('idx_contr_datas', 'contracts', ['start_date', 'end_date'], unique=False)
    op.create_index('idx_contr_tipo', 'contracts', ['contract_type'], unique=False)
    op.create_index('idx_contr_responsavel', 'contracts', ['responsible_id'], unique=False)

    # Legal Processes
    op.create_table('legal_processes',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('process_number', sa.String(length=50), nullable=True),
        sa.Column('process_type', sa.String(length=50), nullable=True, comment='labor, civil, tax'),
        sa.Column('counterparty', sa.String(length=255), nullable=True),
        sa.Column('cause_amount', sa.Numeric(15, 2), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=True, comment='andamento, suspenso, concluido'),
        sa.Column('risk', sa.String(length=20), nullable=True, comment='baixo, medio, alto'),
        sa.Column('court', sa.String(length=100), nullable=True),
        sa.Column('responsible_attorney', sa.String(length=255), nullable=True),
        sa.Column('history', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='[{data, evento, description}]'),
        sa.Column('next_action', sa.Date(), nullable=True),
        sa.Column('next_action_description', sa.Text(), nullable=True),
        sa.Column('document_ids', postgresql.ARRAY(sa.Uuid()), nullable=True, comment='Array de IDs de documents'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('process_number'),
        comment='Processos jurídicos em andamento'
    )
    op.create_index('idx_pj_numero', 'legal_processes', ['process_number'], unique=False)
    op.create_index('idx_pj_empresa', 'legal_processes', ['company_id'], unique=False)
    op.create_index('idx_pj_proxima_acao', 'legal_processes', ['next_action'], unique=False)
    op.create_index('idx_pj_status', 'legal_processes', ['status'], unique=False)
    op.create_index('idx_pj_risco', 'legal_processes', ['risk'], unique=False)

    # ============================================
    # TRIGGERS FOR UPDATED_AT
    # ============================================

    tables_with_updated_at = [
        'documents', 'suppliers', 'accounts_payable', 'corporate_cards',
        'card_invoices', 'card_transactions', 'purchase_orders', 'employees',
        'employment_contracts', 'contracts', 'legal_processes'
    ]

    for table in tables_with_updated_at:
        op.execute(f"""
            CREATE TRIGGER trigger_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at();
        """)


def downgrade() -> None:
    # Drop triggers first
    tables_with_updated_at = [
        'legal_processes', 'contracts', 'employment_contracts', 'employees',
        'purchase_orders', 'card_transactions', 'card_invoices', 'corporate_cards',
        'accounts_payable', 'suppliers', 'documents'
    ]

    for table in tables_with_updated_at:
        op.execute(f"DROP TRIGGER IF EXISTS trigger_{table}_updated_at ON {table}")

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('legal_processes')
    op.drop_table('contracts')
    op.drop_table('employment_contracts')
    op.drop_table('employees')
    op.drop_table('purchase_orders')
    op.drop_table('card_transactions')
    op.drop_table('card_invoices')
    op.drop_table('corporate_cards')
    op.drop_table('accounts_payable')
    op.drop_table('suppliers')
    op.drop_table('cost_centers')
    op.drop_table('documents')
