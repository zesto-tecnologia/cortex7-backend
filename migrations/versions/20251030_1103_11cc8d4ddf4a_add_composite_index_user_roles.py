"""add_composite_index_user_roles

Revision ID: 11cc8d4ddf4a
Revises: 03b858fdc31f
Create Date: 2025-10-30 11:03:57.531562

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '11cc8d4ddf4a'
down_revision: Union[str, Sequence[str], None] = '03b858fdc31f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add composite unique index on user_roles for data integrity and performance."""
    # Add unique constraint to prevent duplicate role assignments
    op.create_unique_constraint(
        "uq_user_roles_user_id_role_id",
        "user_roles",
        ["user_id", "role_id"]
    )

    # Add index for reverse lookups (finding users with a specific role)
    op.create_index(
        "idx_user_roles_role_id_user_id",
        "user_roles",
        ["role_id", "user_id"]
    )


def downgrade() -> None:
    """Remove composite unique index from user_roles."""
    op.drop_index("idx_user_roles_role_id_user_id", "user_roles")
    op.drop_constraint("uq_user_roles_user_id_role_id", "user_roles", type_="unique")
