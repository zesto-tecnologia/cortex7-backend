"""Unified foundation: extensions, auth tables, and corporate core

Revision ID: 001_unified_foundation
Revises:
Create Date: 2025-10-23 15:20:00.000000

This migration combines:
- Extensions (uuid-ossp, vector/pgvector)
- Auth system (users, jwt_keys, refresh_tokens, audit_logs)
- Corporate core (companies, departments, user_profiles)
- User-company relationships
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_unified_foundation'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # EXTENSIONS
    # ============================================
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')

    # ============================================
    # ENUMS
    # ============================================
    # Create enum type with create_type=False to prevent auto-creation
    user_role_enum = postgresql.ENUM('user', 'admin', 'super_admin', name='user_role', create_type=False)
    # Check if the type exists and create if it doesn't
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'user_role'"))
    if not result.fetchone():
        op.execute("CREATE TYPE user_role AS ENUM ('user', 'admin', 'super_admin')")

    # ============================================
    # AUTH TABLES
    # ============================================

    # JWT Keys table
    op.create_table('jwt_keys',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('kid', sa.String(length=255), nullable=False),
        sa.Column('public_key', sa.Text(), nullable=False),
        sa.Column('private_key_ref', sa.String(length=255), nullable=False, comment='Reference to private key in Vault/Secrets Manager'),
        sa.Column('algorithm', sa.String(length=10), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        comment='JWT public/private key pairs for token signing and verification'
    )
    op.create_index(op.f('ix_jwt_keys_active'), 'jwt_keys', ['active'], unique=False)
    op.create_index(op.f('ix_jwt_keys_expires_at'), 'jwt_keys', ['expires_at'], unique=False)
    op.create_index(op.f('ix_jwt_keys_kid'), 'jwt_keys', ['kid'], unique=True)

    # Users table (authentication)
    op.create_table('users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('role', user_role_enum, nullable=False),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('auth_provider', sa.String(length=50), nullable=True, comment='OAuth provider: supabase, google, github, etc'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        comment='Authentication users table - stores auth credentials and basic info'
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    op.create_index(op.f('ix_users_deleted_at'), 'users', ['deleted_at'], unique=False)

    # Audit logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='Authentication audit trail'
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)

    # Refresh tokens table
    op.create_table('refresh_tokens',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('token_family_id', sa.String(length=255), nullable=False, comment='Token family for rotation detection'),
        sa.Column('device_id', sa.String(length=255), nullable=True, comment='Device identifier for tracking'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Refresh tokens for authentication with rotation support'
    )
    op.create_index(op.f('ix_refresh_tokens_expires_at'), 'refresh_tokens', ['expires_at'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=True)
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_token_family_id'), 'refresh_tokens', ['token_family_id'], unique=False)

    # ============================================
    # CORPORATE CORE TABLES
    # ============================================

    # Companies (formerly companies)
    op.create_table('companies',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('tax_id', sa.String(length=14), nullable=False),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Policies, approval limits, business rules'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        comment='Companies using the system'
    )
    op.create_index(op.f('ix_companies_tax_id'), 'companies', ['tax_id'], unique=True)

    # User-Company relationship (multi-tenancy support)
    op.create_table('user_companies',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'company_id'),
        comment='Links auth users to companies for multi-tenancy'
    )
    op.create_index(op.f('ix_user_companies_company_id'), 'user_companies', ['company_id'], unique=False)
    op.create_index(op.f('ix_user_companies_user_id'), 'user_companies', ['user_id'], unique=False)

    # Departments (formerly departments)
    op.create_table('departments',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='HR, Finance, Legal, Procurement'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Departments within each company'
    )
    op.create_index(op.f('ix_departments_company_id'), 'departments', ['company_id'], unique=False)

    # User Profiles (formerly user_profiles - corporate user profiles)
    op.create_table('user_profiles',
        sa.Column('id', sa.Uuid(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.Uuid(), nullable=False, comment='Links to auth users table'),
        sa.Column('company_id', sa.Uuid(), nullable=False),
        sa.Column('department_id', sa.Uuid(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('position', sa.String(length=100), nullable=True),
        sa.Column('approval_limits', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Approval limits by module: {finance: 50000, procurement: 30000}'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        comment='Corporate user profiles with company-specific information'
    )
    op.create_index(op.f('ix_user_profiles_email'), 'user_profiles', ['email'], unique=True)
    op.create_index(op.f('ix_user_profiles_company_id'), 'user_profiles', ['company_id'], unique=False)
    op.create_index(op.f('ix_user_profiles_user_id'), 'user_profiles', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_profiles_status'), 'user_profiles', ['status'], unique=False)

    # ============================================
    # TRIGGERS
    # ============================================

    # Function to auto-update updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Triggers for updated_at on tables
    for table in ['jwt_keys', 'users', 'refresh_tokens', 'companies', 'user_profiles']:
        op.execute(f"""
            CREATE TRIGGER trigger_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at();
        """)


def downgrade() -> None:
    # Drop triggers
    for table in ['user_profiles', 'companies', 'refresh_tokens', 'users', 'jwt_keys']:
        op.execute(f"DROP TRIGGER IF EXISTS trigger_{table}_updated_at ON {table}")

    # Drop function
    op.execute("DROP FUNCTION IF EXISTS update_updated_at()")

    # Drop tables (reverse order of creation)
    op.drop_table('user_profiles')
    op.drop_table('departments')
    op.drop_table('user_companies')
    op.drop_table('companies')
    op.drop_table('refresh_tokens')
    op.drop_table('audit_logs')
    op.drop_table('users')
    op.drop_table('jwt_keys')

    # Drop enum
    op.execute("DROP TYPE IF EXISTS user_role")

    # Drop extensions
    op.execute('DROP EXTENSION IF EXISTS "vector"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')