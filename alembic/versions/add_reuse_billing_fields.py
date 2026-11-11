"""add reuse and billing_period fields

Revision ID: add_reuse_billing_fields
Revises: merge_all_heads
Create Date: 2026-11-15
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_reuse_billing_fields'
down_revision = 'merge_all_heads'
branch_labels = None
depends_on = None


def upgrade():
    # Verification reuse fields (REV-002 / OPEN-3)
    with op.batch_alter_table('verifications') as batch_op:
        batch_op.add_column(sa.Column('reusable_until', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('reused_from_id', sa.String(), nullable=True))

    # Subscription billing period (REV-001)
    with op.batch_alter_table('subscriptions') as batch_op:
        batch_op.add_column(sa.Column('billing_period', sa.String(10), nullable=False, server_default='monthly'))
        batch_op.add_column(sa.Column('annual_renewal_at', sa.DateTime(), nullable=True))

    # Rental expiry warning (INV-003)
    with op.batch_alter_table('rentals') as batch_op:
        batch_op.add_column(sa.Column('expiry_warned_at', sa.DateTime(), nullable=True))

    # Stock watches table (INV-001)
    op.create_table(
        'stock_watches',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('service_name', sa.String(100), nullable=False),
        sa.Column('capability', sa.String(20), nullable=False, server_default='sms'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('notified_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('user_id', 'service_name', 'capability', name='uq_stock_watch'),
    )
    op.create_index('ix_stock_watches_user_id', 'stock_watches', ['user_id'])
    op.create_index('ix_stock_watches_service_name', 'stock_watches', ['service_name'])

    # Rental back orders table (INV-002)
    op.create_table(
        'rental_back_orders',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tv_back_order_id', sa.String(100), nullable=False, unique=True),
        sa.Column('service_name', sa.String(100), nullable=False),
        sa.Column('capability', sa.String(20), nullable=False, server_default='sms'),
        sa.Column('requested_at', sa.DateTime(), nullable=False),
        sa.Column('fulfilled_at', sa.DateTime(), nullable=True),
        sa.Column('notified_at', sa.DateTime(), nullable=True),
        sa.Column('credits_held', sa.Numeric(10, 4), nullable=False),
    )
    op.create_index('ix_rental_back_orders_user_id', 'rental_back_orders', ['user_id'])


def downgrade():
    op.drop_table('rental_back_orders')
    op.drop_table('stock_watches')
    with op.batch_alter_table('rentals') as batch_op:
        batch_op.drop_column('expiry_warned_at')
    with op.batch_alter_table('subscriptions') as batch_op:
        batch_op.drop_column('annual_renewal_at')
        batch_op.drop_column('billing_period')
    with op.batch_alter_table('verifications') as batch_op:
        batch_op.drop_column('reused_from_id')
        batch_op.drop_column('reusable_until')
