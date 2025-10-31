"""update_integers_to_bigint_for_omie_ids

Revision ID: 0f804052c115
Revises: fda0640e30da
Create Date: 2025-10-27 16:08:36.566712

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0f804052c115'
down_revision = 'fda0640e30da'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Alter dim_clients.omie_client_id from INTEGER to BIGINT
    op.alter_column(
        "dim_clients",
        "omie_client_id",
        existing_type=sa.INTEGER(),
        type_=sa.BigInteger(),
        existing_nullable=False,
    )

    # Alter dim_cost_centers.omie_cc_id from INTEGER to BIGINT
    op.alter_column(
        "dim_cost_centers",
        "omie_cc_id",
        existing_type=sa.INTEGER(),
        type_=sa.BigInteger(),
        existing_nullable=True,
    )

    # Alter fact_financial_transactions columns
    columns_to_alter = [
        "omie_title_id",
        "omie_contract_id",
        "omie_service_order_id",
        "omie_invoice_id",
        "omie_payment_id",
        "omie_payment_cc_id",
    ]

    for column_name in columns_to_alter:
        op.alter_column(
            "fact_financial_transactions",
            column_name,
            existing_type=sa.INTEGER(),
            type_=sa.BigInteger(),
            existing_nullable=True if column_name != "omie_title_id" else False,
        )


def downgrade() -> None:
    # Reverse: Alter back to INTEGER (may cause data loss if values exceed int32 range)
    op.alter_column(
        "dim_clients",
        "omie_client_id",
        existing_type=sa.BigInteger(),
        type_=sa.INTEGER(),
        existing_nullable=False,
    )

    op.alter_column(
        "dim_cost_centers",
        "omie_cc_id",
        existing_type=sa.BigInteger(),
        type_=sa.INTEGER(),
        existing_nullable=True,
    )

    columns_to_alter = [
        "omie_title_id",
        "omie_contract_id",
        "omie_service_order_id",
        "omie_invoice_id",
        "omie_payment_id",
        "omie_payment_cc_id",
    ]

    for column_name in columns_to_alter:
        op.alter_column(
            "fact_financial_transactions",
            column_name,
            existing_type=sa.BigInteger(),
            type_=sa.INTEGER(),
            existing_nullable=True if column_name != "omie_title_id" else False,
        )
