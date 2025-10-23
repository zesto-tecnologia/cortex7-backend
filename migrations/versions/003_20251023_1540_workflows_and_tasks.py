"""Unified workflow and task system

Revision ID: 003_workflows_and_tasks
Revises: 002_corporate_modules
Create Date: 2025-10-23 15:40:00.000000

This migration resolves the duplicate workflows/tasks issue by creating:
- corporate_workflows: Business workflows with phases and configuration
- ai_workflows: AI agent workflows with Celery task tracking
- tasks: Unified task table supporting both workflow types
- Functions for automatic deadline calculation
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_workflows_and_tasks'
down_revision = '002_corporate_modules'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # WORKFLOW TYPE ENUM
    # ============================================
    # Create enum type with create_type=False to prevent auto-creation
    workflow_type_enum = postgresql.ENUM('corporate', 'ai', name='workflow_type', create_type=False)
    # Check if the type exists and create if it doesn't
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'workflow_type'"))
    if not result.fetchone():
        op.execute("CREATE TYPE workflow_type AS ENUM ('corporate', 'ai')")

    # ============================================
    # CORPORATE WORKFLOWS
    # ============================================
    op.create_table('corporate_workflows',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False, comment='contratacao, compra, aprovacao_contrato'),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('phases', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='[{name, ordem, responsavel, acoes}]'),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Workflows configuráveis do sistema corporativo'
    )
    op.create_index('idx_wf_corp_empresa', 'corporate_workflows', ['company_id'], unique=False)
    op.create_index('idx_wf_corp_tipo', 'corporate_workflows', ['type'], unique=False)
    op.create_index('idx_wf_corp_ativo', 'corporate_workflows', ['active'], unique=False)

    # ============================================
    # AI WORKFLOWS
    # ============================================
    op.create_table('ai_workflows',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('workflow_type', sa.String(length=100), nullable=False, comment='document_extraction, task_ranking, etc'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending', comment='pending, processing, completed, failed'),
        sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Input parameters for the AI workflow'),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Workflow execution result'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('celery_task_id', sa.String(length=100), nullable=True, comment='Celery async task ID'),
        sa.Column('priority', sa.String(length=10), nullable=False, server_default='normal', comment='low, normal, high'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('celery_task_id'),
        comment='AI agent workflows with Celery integration'
    )
    op.create_index('idx_wf_ai_empresa', 'ai_workflows', ['company_id'], unique=False)
    op.create_index('idx_wf_ai_workflow_type', 'ai_workflows', ['workflow_type'], unique=False)
    op.create_index('idx_wf_ai_status', 'ai_workflows', ['status'], unique=False)
    op.create_index('idx_wf_ai_celery_task', 'ai_workflows', ['celery_task_id'], unique=False)

    # ============================================
    # UNIFIED TASKS TABLE
    # ============================================
    op.create_table('tasks',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('workflow_type', workflow_type_enum, nullable=True, comment='Type of workflow: corporate or ai'),
        sa.Column('workflow_corporate_id', sa.Uuid(), nullable=True, comment='Reference to corporate workflow'),
        sa.Column('workflow_ai_id', sa.Uuid(), nullable=True, comment='Reference to AI workflow'),
        sa.Column('entity_type', sa.String(length=50), nullable=True, comment='ordem_compra, contrato, funcionario'),
        sa.Column('entity_id', sa.Uuid(), nullable=True, comment='ID of the related entity'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('responsible_id', sa.Uuid(), nullable=True, comment='User responsible for the task'),
        sa.Column('assigned_to', sa.Uuid(), nullable=True, comment='User assigned to the task (AI workflows)'),
        sa.Column('department', sa.String(length=50), nullable=True, comment='Department responsible'),
        sa.Column('type', sa.String(length=50), nullable=True, comment='Task type classification'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pendente', comment='pendente, em_andamento, bloqueada, concluida, cancelada'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='5', comment='1=crítico, 5=normal, 10=baixo'),
        sa.Column('deadline', sa.Date(), nullable=True, comment='Task deadline'),
        sa.Column('legal_deadline', sa.Boolean(), nullable=False, server_default='false', comment='Indicates if deadline has legal implications'),
        sa.Column('days_until_due', sa.Integer(), nullable=True, comment='Days until deadline (auto-calculated)'),
        sa.Column('dependencies', postgresql.ARRAY(sa.Uuid()), nullable=True, comment='Array of task UUIDs that block this one'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Additional metadata'),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Task result (AI workflows)'),
        sa.Column('due_date', sa.String(length=50), nullable=True, comment='Due date string (AI workflows)'),
        sa.Column('completed_at', sa.Date(), nullable=True, comment='Date when task was completed'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workflow_corporate_id'], ['corporate_workflows.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['workflow_ai_id'], ['ai_workflows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['responsible_id'], ['user_profiles.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_to'], ['user_profiles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='Unified tasks table supporting both corporate and AI workflows'
    )

    # Create indexes for tasks
    op.create_index('idx_tasks_ranking', 'tasks', ['status', 'priority', 'deadline', 'department'], unique=False, postgresql_where=sa.text("status != 'concluida'"))
    op.create_index('idx_tar_empresa', 'tasks', ['company_id'], unique=False)
    op.create_index('idx_tar_responsavel', 'tasks', ['responsible_id'], unique=False)
    op.create_index('idx_tar_atribuido', 'tasks', ['assigned_to'], unique=False)
    op.create_index('idx_tar_wf_corporate', 'tasks', ['workflow_corporate_id'], unique=False)
    op.create_index('idx_tar_wf_ai', 'tasks', ['workflow_ai_id'], unique=False)
    op.create_index('idx_tar_status', 'tasks', ['status'], unique=False)
    op.create_index('idx_tar_prazo', 'tasks', ['deadline'], unique=False, postgresql_where=sa.text('deadline IS NOT NULL'))

    # ============================================
    # FUNCTIONS AND TRIGGERS
    # ============================================

    # Function to auto-calculate days_until_due
    op.execute("""
        CREATE OR REPLACE FUNCTION calculate_days_until_due()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.deadline IS NOT NULL THEN
                NEW.days_until_due := (NEW.deadline - CURRENT_DATE);
            ELSE
                NEW.days_until_due := NULL;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Trigger for tasks to auto-calculate days_until_due
    op.execute("""
        CREATE TRIGGER trigger_tasks_dias_vencimento
        BEFORE INSERT OR UPDATE OF deadline ON tasks
        FOR EACH ROW
        EXECUTE FUNCTION calculate_days_until_due();
    """)

    # Triggers for updated_at
    for table in ['corporate_workflows', 'ai_workflows', 'tasks']:
        op.execute(f"""
            CREATE TRIGGER trigger_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at();
        """)


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS trigger_tasks_dias_vencimento ON tasks")

    for table in ['tasks', 'ai_workflows', 'corporate_workflows']:
        op.execute(f"DROP TRIGGER IF EXISTS trigger_{table}_updated_at ON {table}")

    # Drop function
    op.execute("DROP FUNCTION IF EXISTS calculate_days_until_due()")

    # Drop tables (reverse order)
    op.drop_table('tasks')
    op.drop_table('ai_workflows')
    op.drop_table('corporate_workflows')

    # Drop enum
    op.execute("DROP TYPE IF EXISTS workflow_type")
