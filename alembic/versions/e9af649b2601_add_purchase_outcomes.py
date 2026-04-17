"""add_purchase_outcomes

Revision ID: e9af649b2601
Revises: 061d9956377d
Create Date: 2026-04-17 17:18:40.963516

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e9af649b2601'
down_revision = '061d9956377d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if table already exists (idempotency)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not inspector.has_table('purchase_outcomes'):
        op.create_table(
            'purchase_outcomes',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('service', sa.String(length=100), nullable=False),
            sa.Column('requested_code', sa.String(length=10), nullable=True),
            sa.Column('assigned_code', sa.String(length=10), nullable=False),
            sa.Column('assigned_carrier', sa.String(length=50), nullable=True),
            sa.Column('carrier_type', sa.String(length=20), nullable=True),
            sa.Column('assigned_city', sa.String(length=100), nullable=True),
            sa.Column('assigned_state', sa.String(length=2), nullable=True),
            sa.Column('matched', sa.Boolean(), nullable=True),
            sa.Column('sms_received', sa.Boolean(), nullable=True),
            sa.Column('user_id', sa.String(), nullable=True), # Users might not have rigorous FK constraints in this phase or we might use ForeignKey
            sa.Column('verification_id', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('hour_utc', sa.SmallInteger(), nullable=True),
            sa.Column('day_of_week', sa.SmallInteger(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['verification_id'], ['verifications.id'], ondelete='SET NULL')
        )
        
        op.create_index('ix_purchase_outcomes_service', 'purchase_outcomes', ['service'])
        op.create_index('ix_purchase_outcomes_created_at', 'purchase_outcomes', ['created_at'])
        
        # Composite indexes
        op.create_index('ix_po_svc_assigned_date', 'purchase_outcomes', ['service', 'assigned_code', 'created_at'])
        op.create_index('ix_po_svc_requested_date', 'purchase_outcomes', ['service', 'requested_code', 'created_at'])
        op.create_index('ix_po_carrier_svc', 'purchase_outcomes', ['assigned_carrier', 'service'])


def downgrade() -> None:
    op.drop_index('ix_po_carrier_svc', table_name='purchase_outcomes')
    op.drop_index('ix_po_svc_requested_date', table_name='purchase_outcomes')
    op.drop_index('ix_po_svc_assigned_date', table_name='purchase_outcomes')
    op.drop_index('ix_purchase_outcomes_created_at', table_name='purchase_outcomes')
    op.drop_index('ix_purchase_outcomes_service', table_name='purchase_outcomes')
    op.drop_table('purchase_outcomes')