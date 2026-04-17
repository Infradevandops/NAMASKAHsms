"""add_financial_telemetry_to_outcomes
 
Revision ID: 8a288c52a5d4
Revises: a1b2c3d4e5f6
Create Date: 2026-04-17 22:37:35.990195
 
"""
from alembic import op
import sqlalchemy as sa
 
revision = '8a288c52a5d4'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None
 
def _column_exists(table, column):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns(table)]
    return column in columns
 
def upgrade() -> None:
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('purchase_outcomes', schema=None) as batch_op:
        # 1. Institutional Telemetry (Catch-up)
        if not _column_exists('purchase_outcomes', 'provider'):
            batch_op.add_column(sa.Column('provider', sa.String(50), nullable=True))
        if not _column_exists('purchase_outcomes', 'country'):
            batch_op.add_column(sa.Column('country', sa.String(5), nullable=True))
        if not _column_exists('purchase_outcomes', 'raw_sms_code'):
            batch_op.add_column(sa.Column('raw_sms_code', sa.String(50), nullable=True))
        if not _column_exists('purchase_outcomes', 'latency_seconds'):
            batch_op.add_column(sa.Column('latency_seconds', sa.Float(), nullable=True))
        else:
            # If it exists (e.g. from an older partial migration), ensured it is Float
            batch_op.alter_column('latency_seconds', type_=sa.Float())
 
        # 2. Financial Telemetry
        if not _column_exists('purchase_outcomes', 'is_refunded'):
            batch_op.add_column(sa.Column('is_refunded', sa.Boolean(), server_default='0', nullable=True))
        if not _column_exists('purchase_outcomes', 'refund_amount'):
            batch_op.add_column(sa.Column('refund_amount', sa.Float(), server_default='0.0', nullable=True))
        if not _column_exists('purchase_outcomes', 'provider_cost'):
            batch_op.add_column(sa.Column('provider_cost', sa.Float(), nullable=True))
        if not _column_exists('purchase_outcomes', 'user_price'):
            batch_op.add_column(sa.Column('user_price', sa.Float(), nullable=True))
 
        # 3. Indexes
        batch_op.create_index('ix_purchase_outcomes_is_refunded', ['is_refunded'])
        batch_op.create_index('ix_purchase_outcomes_provider', ['provider'])
        batch_op.create_index('ix_purchase_outcomes_country', ['country'])
 
def downgrade() -> None:
    with op.batch_alter_table('purchase_outcomes', schema=None) as batch_op:
        batch_op.drop_index('ix_purchase_outcomes_country')
        batch_op.drop_index('ix_purchase_outcomes_provider')
        batch_op.drop_index('ix_purchase_outcomes_is_refunded')
        batch_op.drop_column('user_price')
        batch_op.drop_column('provider_cost')
        batch_op.drop_column('refund_amount')
        batch_op.drop_column('is_refunded')
        batch_op.drop_column('latency_seconds')
        batch_op.drop_column('raw_sms_code')
        batch_op.drop_column('country')
        batch_op.drop_column('provider')