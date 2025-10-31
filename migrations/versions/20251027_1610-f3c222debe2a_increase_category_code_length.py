"""increase_category_code_length

Revision ID: f3c222debe2a
Revises: 0f804052c115
Create Date: 2025-10-27 16:10:53.675338

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3c222debe2a'
down_revision = '0f804052c115'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Increase category_code length from VARCHAR(50) to VARCHAR(255)
    op.alter_column(
        "dim_categories",
        "category_code",
        existing_type=sa.String(length=50),
        type_=sa.String(length=255),
        existing_nullable=False,
    )


def downgrade() -> None:
    # Reverse: Decrease category_code length back to VARCHAR(50)
    op.alter_column(
        "dim_categories",
        "category_code",
        existing_type=sa.String(length=255),
        type_=sa.String(length=50),
        existing_nullable=False,
    )
