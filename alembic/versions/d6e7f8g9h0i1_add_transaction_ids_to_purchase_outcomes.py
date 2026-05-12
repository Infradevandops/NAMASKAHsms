"""add transaction ids to purchase outcomes

Revision ID: d6e7f8g9h0i1
Revises: a1b2c3d4e5f6
Create Date: 2026-03-20 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "d6e7f8g9h0i1"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("purchase_outcomes", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("debit_transaction_id", sa.String(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("refund_transaction_id", sa.String(), nullable=True)
        )

    # Add foreign keys in separate batch operations
    with op.batch_alter_table("purchase_outcomes", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "fk_purchase_outcomes_debit_transaction",
            "balance_transactions",
            ["debit_transaction_id"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("purchase_outcomes", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "fk_purchase_outcomes_refund_transaction",
            "balance_transactions",
            ["refund_transaction_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade():
    with op.batch_alter_table("purchase_outcomes", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_purchase_outcomes_refund_transaction", type_="foreignkey"
        )
        batch_op.drop_constraint(
            "fk_purchase_outcomes_debit_transaction", type_="foreignkey"
        )
        batch_op.drop_column("refund_transaction_id")
        batch_op.drop_column("debit_transaction_id")
