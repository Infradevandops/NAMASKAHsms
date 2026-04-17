"""add refund_reason to purchase_outcomes

Revision ID: 7fabde7ccee5
Revises: 8a288c52a5d4
Create Date: 2026-04-17 22:54:16.213653

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7fabde7ccee5'
down_revision = '8a288c52a5d4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use inspector for Brutal Stability
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("purchase_outcomes")]

    if "refund_reason" not in columns:
        with op.batch_alter_table("purchase_outcomes") as batch_op:
            batch_op.add_column(sa.Column("refund_reason", sa.String(length=100), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("purchase_outcomes") as batch_op:
        batch_op.drop_column("refund_reason")