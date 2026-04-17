"""add phase 10 reconciliation fields to purchase_outcomes

Revision ID: b1279f965154
Revises: 7fabde7ccee5
Create Date: 2026-04-17 23:03:31.213653

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1279f965154'
down_revision = '7fabde7ccee5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use inspector for Brutal Stability
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("purchase_outcomes")]

    with op.batch_alter_table("purchase_outcomes") as batch_op:
        if "provider_refunded" not in columns:
            batch_op.add_column(sa.Column("provider_refunded", sa.Boolean(), nullable=True, server_default="0"))
        if "outcome_category" not in columns:
            batch_op.add_column(sa.Column("outcome_category", sa.String(length=20), nullable=True))
        if "provider_error_code" not in columns:
            batch_op.add_column(sa.Column("provider_error_code", sa.String(length=50), nullable=True))

    # Add indices for performance
    if "provider_refunded" in columns:
        op.create_index("ix_purchase_outcomes_provider_refunded", "purchase_outcomes", ["provider_refunded"])
    if "outcome_category" in columns:
        op.create_index("ix_purchase_outcomes_outcome_category", "purchase_outcomes", ["outcome_category"])


def downgrade() -> None:
    op.drop_index("ix_purchase_outcomes_outcome_category", table_name="purchase_outcomes")
    op.drop_index("ix_purchase_outcomes_provider_refunded", table_name="purchase_outcomes")
    with op.batch_alter_table("purchase_outcomes") as batch_op:
        batch_op.drop_column("provider_error_code")
        batch_op.drop_column("outcome_category")
        batch_op.drop_column("provider_refunded")