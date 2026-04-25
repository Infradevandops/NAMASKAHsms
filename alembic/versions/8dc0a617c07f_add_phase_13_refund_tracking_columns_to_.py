"""add phase 13 refund tracking columns to purchase outcomes

Revision ID: 8dc0a617c07f
Revises: a1abc40e4d61
Create Date: 2026-04-25 02:28:18.378706

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8dc0a617c07f'
down_revision = 'a1abc40e4d61'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if columns already exist (idempotent)
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    if "purchase_outcomes" not in inspector.get_table_names():
        return
    
    existing_columns = [col["name"] for col in inspector.get_columns("purchase_outcomes")]
    
    # Add refund_requested_at if not exists
    if "refund_requested_at" not in existing_columns:
        op.add_column('purchase_outcomes',
            sa.Column('refund_requested_at', sa.DateTime(timezone=True), nullable=True)
        )
    
    # Add refund_processed_at if not exists
    if "refund_processed_at" not in existing_columns:
        op.add_column('purchase_outcomes',
            sa.Column('refund_processed_at', sa.DateTime(timezone=True), nullable=True)
        )
    
    # Add refund_latency_seconds if not exists
    if "refund_latency_seconds" not in existing_columns:
        op.add_column('purchase_outcomes',
            sa.Column('refund_latency_seconds', sa.Float(), nullable=True)
        )


def downgrade() -> None:
    op.drop_column('purchase_outcomes', 'refund_latency_seconds')
    op.drop_column('purchase_outcomes', 'refund_processed_at')
    op.drop_column('purchase_outcomes', 'refund_requested_at')