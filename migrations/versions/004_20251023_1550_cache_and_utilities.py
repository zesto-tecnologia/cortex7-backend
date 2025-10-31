"""Cache, utilities, views and agent system

Revision ID: 004_cache_and_utilities
Revises: 003_workflows_and_tasks
Create Date: 2025-10-23 15:50:00.000000

This migration adds:
- Agent logging system (agent_logs)
- Corporate audit trail (audit_trail - separate from auth audit_logs)
- Embedding cache for performance
- Agent configuration system
- Business views for dashboards and metrics
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_cache_and_utilities'
down_revision = '003_workflows_and_tasks'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # AGENT LOGGING
    # ============================================
    op.create_table('agent_logs',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), nullable=True),
        sa.Column('agent_type', sa.String(length=50), nullable=False, comment='ranqueador, gerador, atuador, validador, extrator, conversacional, orquestrador'),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=True, comment='tarefa, documento, ordem_compra'),
        sa.Column('entity_id', sa.Uuid(), nullable=True),
        sa.Column('input', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='O que foi enviado ao agente'),
        sa.Column('output', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='O que o agente retornou'),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Log de execução dos agentes de IA'
    )
    op.create_index('idx_logs_agente_tipo', 'agent_logs', ['agent_type'], unique=False)
    op.create_index('idx_logs_empresa', 'agent_logs', ['company_id'], unique=False)
    op.create_index('idx_logs_created', 'agent_logs', ['created_at'], unique=False)
    op.execute('CREATE INDEX idx_logs_sucesso ON agent_logs(success) WHERE NOT success')

    # ============================================
    # CORPORATE AUDIT
    # ============================================
    op.create_table('audit_trail',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), nullable=True),
        sa.Column('user_profile_id', sa.Uuid(), nullable=True),
        sa.Column('table_name', sa.String(length=50), nullable=False),
        sa.Column('record_id', sa.Uuid(), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=False, comment='INSERT, UPDATE, DELETE'),
        sa.Column('previous_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_profile_id'], ['user_profiles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='Auditoria completa de mudanças no sistema corporativo'
    )
    op.create_index('idx_audit_tabela', 'audit_trail', ['table_name'], unique=False)
    op.create_index('idx_audit_registro', 'audit_trail', ['record_id'], unique=False)
    op.create_index('idx_audit_created', 'audit_trail', ['created_at'], unique=False)
    op.create_index('idx_audit_empresa', 'audit_trail', ['company_id'], unique=False)
    op.create_index('idx_audit_usuario', 'audit_trail', ['user_profile_id'], unique=False)

    # ============================================
    # EMBEDDING CACHE
    # ============================================
    op.create_table('embedding_cache',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('hash', sa.String(length=64), nullable=False, comment='Hash SHA-256 do text'),
        sa.Column('model', sa.String(length=50), nullable=False, server_default='text-embedding-ada-002'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('hash'),
        comment='Cache de embeddings para evitar reprocessamento'
    )

    # Add embedding vector column using raw SQL
    op.execute('ALTER TABLE embedding_cache ADD COLUMN embedding vector(1536) NOT NULL')

    # Create indexes
    op.create_index('idx_cache_hash', 'embedding_cache', ['hash'], unique=False)
    op.create_index('idx_cache_created', 'embedding_cache', ['created_at'], unique=False)

    # ============================================
    # AGENT CONFIGURATION
    # ============================================
    op.create_table('agent_configs',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), nullable=True),
        sa.Column('agent_type', sa.String(length=50), nullable=False),
        sa.Column('configuration', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='Configuração JSON específica para cada type de agente'),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Configurações dos agentes de IA por empresa'
    )
    op.create_index('idx_agconfig_empresa', 'agent_configs', ['company_id'], unique=False)
    op.create_index('idx_agconfig_tipo', 'agent_configs', ['agent_type'], unique=False)
    op.create_index('idx_agconfig_ativo', 'agent_configs', ['active'], unique=False)

    # ============================================
    # BUSINESS VIEWS
    # ============================================

    # View: Contracts with calculated status
    op.execute("""
        CREATE VIEW contracts_with_real_status AS
        SELECT
            c.*,

            -- Dynamically calculated status
            CASE
                WHEN c.status IN ('rascunho', 'aprovacao') THEN 'nao_vigente'
                WHEN c.status IN ('rescindido', 'encerrado') THEN 'nao_vigente'
                WHEN c.start_date > CURRENT_DATE THEN 'nao_vigente'
                WHEN c.end_date IS NULL THEN 'vigente'
                WHEN c.end_date >= CURRENT_DATE THEN 'vigente'
                WHEN c.end_date < CURRENT_DATE AND c.auto_renewal THEN 'vigente_renovado'
                ELSE 'vencido'
            END as status_calculado,

            -- Alerts
            CASE
                WHEN c.end_date IS NOT NULL AND c.end_date - CURRENT_DATE <= 30 THEN true
                ELSE false
            END as vence_em_30_dias,

            CASE
                WHEN c.end_date IS NOT NULL AND c.end_date - CURRENT_DATE <= 90 THEN true
                ELSE false
            END as vence_em_90_dias,

            -- Days until expiration
            CASE
                WHEN c.end_date IS NOT NULL THEN c.end_date - CURRENT_DATE
            END as days_until_due

        FROM contracts c
    """)

    # View: Corporate cards dashboard
    op.execute("""
        CREATE VIEW cards_dashboard AS
        SELECT
            c.id,
            c.masked_number,
            c.company_id,
            u.name as portador,
            c.credit_limit,
            c.available_credit,
            COALESCE(f_aberta.total_amount, 0) as fatura_atual,
            COUNT(l.id) FILTER (WHERE NOT l.approved) as lancamentos_pendentes,
            SUM(l.amount) FILTER (WHERE NOT l.approved) as valor_pendente_aprovacao
        FROM corporate_cards c
        LEFT JOIN user_profiles u ON c.cardholder_id = u.id
        LEFT JOIN card_invoices f_aberta ON f_aberta.card_id = c.id
            AND f_aberta.status = 'aberta'
        LEFT JOIN card_transactions l ON l.card_id = c.id
            AND l.invoice_id = f_aberta.id
        WHERE c.status = 'active'
        GROUP BY c.id, c.masked_number, c.company_id, u.name, c.credit_limit, c.available_credit, f_aberta.total_amount
    """)

    # View: General dashboard metrics
    op.execute("""
        CREATE VIEW metrics_dashboard AS
        SELECT
            COUNT(*) FILTER (WHERE status = 'pendente') as tarefas_pendentes,
            COUNT(*) FILTER (WHERE status = 'pendente' AND deadline < CURRENT_DATE) as tarefas_atrasadas,
            COUNT(*) FILTER (WHERE legal_deadline AND deadline <= CURRENT_DATE + 3) as prazos_legais_proximos,
            COUNT(*) FILTER (WHERE status = 'em_andamento') as tarefas_em_andamento
        FROM tasks
        WHERE status != 'concluida'
    """)

    # View: Accounts payable due soon
    op.execute("""
        CREATE VIEW accounts_payable_due_soon AS
        SELECT
            cp.*,
            f.company_name as fornecedor_nome,
            cp.due_date - CURRENT_DATE as days_until_due,
            CASE
                WHEN cp.due_date < CURRENT_DATE THEN 'vencido'
                WHEN cp.due_date = CURRENT_DATE THEN 'vence_hoje'
                WHEN cp.due_date <= CURRENT_DATE + 7 THEN 'vence_semana'
                WHEN cp.due_date <= CURRENT_DATE + 30 THEN 'vence_mes'
                ELSE 'normal'
            END as urgencia
        FROM accounts_payable cp
        LEFT JOIN suppliers f ON cp.supplier_id = f.id
        WHERE cp.status IN ('pendente', 'approved')
            AND cp.due_date <= CURRENT_DATE + 30
        ORDER BY cp.due_date ASC, cp.priority ASC
    """)

    # ============================================
    # TRIGGERS FOR UPDATED_AT
    # ============================================

    # Trigger for agent_configs
    op.execute("""
        CREATE TRIGGER trigger_agent_configs_updated_at
        BEFORE UPDATE ON agent_configs
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at();
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS trigger_agent_configs_updated_at ON agent_configs")

    # Drop views
    op.execute("DROP VIEW IF EXISTS accounts_payable_due_soon")
    op.execute("DROP VIEW IF EXISTS metrics_dashboard")
    op.execute("DROP VIEW IF EXISTS cards_dashboard")
    op.execute("DROP VIEW IF EXISTS contracts_with_real_status")

    # Drop tables (reverse order)
    op.drop_table('agent_configs')
    op.drop_table('embedding_cache')
    op.drop_table('audit_trail')
    op.drop_table('agent_logs')
