"""Rename Portuguese tables to English after refactoring

Revision ID: 006_rename_pt_to_en
Revises: 005_20251023_1600_seed_data
Create Date: 2025-10-24 10:00:00.000000

This migration renames tables from Portuguese to English:
- legal_processes → lawsuits
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_rename_pt_to_en'
down_revision = '005_seed_data'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Rename tables from Portuguese to English."""

    # Rename legal_processes to lawsuits
    op.rename_table('legal_processes', 'lawsuits')

    # Update indexes to match new table name
    op.drop_index('idx_pj_numero', table_name='lawsuits')
    op.drop_index('idx_pj_empresa', table_name='lawsuits')
    op.drop_index('idx_pj_proxima_acao', table_name='lawsuits')
    op.drop_index('idx_pj_status', table_name='lawsuits')
    op.drop_index('idx_pj_risco', table_name='lawsuits')

    # Create new indexes with English naming convention
    op.create_index('idx_lawsuit_number', 'lawsuits', ['process_number'], unique=False)
    op.create_index('idx_lawsuit_company', 'lawsuits', ['company_id'], unique=False)
    op.create_index('idx_lawsuit_next_action', 'lawsuits', ['next_action'], unique=False)
    op.create_index('idx_lawsuit_status', 'lawsuits', ['status'], unique=False)
    op.create_index('idx_lawsuit_risk', 'lawsuits', ['risk'], unique=False)

    # Update any foreign key constraints that reference the old table name
    # This is typically handled automatically by rename_table, but we ensure completeness

    print("✅ Renamed legal_processes table to lawsuits")
    print("✅ Updated all related indexes")


def downgrade() -> None:
    """Revert table names back to Portuguese."""

    # Drop new indexes
    op.drop_index('idx_lawsuit_number', table_name='lawsuits')
    op.drop_index('idx_lawsuit_company', table_name='lawsuits')
    op.drop_index('idx_lawsuit_next_action', table_name='lawsuits')
    op.drop_index('idx_lawsuit_status', table_name='lawsuits')
    op.drop_index('idx_lawsuit_risk', table_name='lawsuits')

    # Rename back to Portuguese
    op.rename_table('lawsuits', 'legal_processes')

    # Recreate original indexes
    op.create_index('idx_pj_numero', 'legal_processes', ['process_number'], unique=False)
    op.create_index('idx_pj_empresa', 'legal_processes', ['company_id'], unique=False)
    op.create_index('idx_pj_proxima_acao', 'legal_processes', ['next_action'], unique=False)
    op.create_index('idx_pj_status', 'legal_processes', ['status'], unique=False)
    op.create_index('idx_pj_risco', 'legal_processes', ['risk'], unique=False)

    print("⏪ Reverted lawsuits table back to legal_processes")