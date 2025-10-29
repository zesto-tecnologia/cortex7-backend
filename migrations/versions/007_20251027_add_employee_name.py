"""Add name column to employees table

Revision ID: 007_add_employee_name
Revises: 006_20251024_rename_pt_to_en
Create Date: 2025-10-27 15:30:00.000000

This migration adds a 'name' column to the employees table
to store the employee's full name directly (not just in JSON).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007_add_employee_name'
down_revision = '006_rename_pt_to_en'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add name column to employees table
    op.add_column('employees',
        sa.Column('name', sa.String(length=255), nullable=True)
    )

    # Migrate existing data: extract name from personal_data JSON
    op.execute("""
        UPDATE employees
        SET name = personal_data->>'full_name'
        WHERE personal_data IS NOT NULL
        AND personal_data->>'full_name' IS NOT NULL
    """)

    # Create index on name for search performance
    op.create_index(
        op.f('ix_employees_name'),
        'employees',
        ['name'],
        unique=False
    )


def downgrade() -> None:
    # Drop index first
    op.drop_index(op.f('ix_employees_name'), table_name='employees')

    # Drop the name column
    op.drop_column('employees', 'name')
