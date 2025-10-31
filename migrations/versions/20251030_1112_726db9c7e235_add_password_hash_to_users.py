"""add_password_hash_to_users

Revision ID: 726db9c7e235
Revises: 11cc8d4ddf4a
Create Date: 2025-10-30 11:12:42.521477

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '726db9c7e235'
down_revision: Union[str, Sequence[str], None] = '11cc8d4ddf4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add password_hash column to users table."""
    op.add_column('users', sa.Column('password_hash', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Remove password_hash column from users table."""
    op.drop_column('users', 'password_hash')
