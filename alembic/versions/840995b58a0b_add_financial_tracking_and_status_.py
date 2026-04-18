"""add financial tracking and status columns

Revision ID: 840995b58a0b
Revises: b1279f965154
Create Date: 2026-04-18 01:50:34.647243

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '840995b58a0b'
down_revision = 'b1279f965154'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add financial tracking and detailed status columns."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('verifications')]

    # Add transaction linking columns
    if 'debit_transaction_id' not in columns:
        op.add_column('verifications', sa.Column(
            'debit_transaction_id',
            sa.String(),
            nullable=True,
            comment='Links to balance_transactions debit record'
        ))
    
    if 'refund_transaction_id' not in columns:
        op.add_column('verifications', sa.Column(
            'refund_transaction_id',
            sa.String(),
            nullable=True,
            comment='Links to balance_transactions refund record'
        ))
    
    # Add detailed status tracking columns
    if 'failure_reason' not in columns:
        op.add_column('verifications', sa.Column(
            'failure_reason',
            sa.String(100),
            nullable=True,
            comment='Specific failure reason code (e.g., user_cancelled, number_unavailable)'
        ))
    
    if 'failure_category' not in columns:
        op.add_column('verifications', sa.Column(
            'failure_category',
            sa.String(50),
            nullable=True,
            comment='Failure category (user_action, provider_issue, system_validation, etc.)'
        ))
    
    # Add SMS receipt tracking
    if 'sms_received' not in columns:
        op.add_column('verifications', sa.Column(
            'sms_received',
            sa.Boolean(),
            server_default='false',
            nullable=False,
            comment='Whether SMS code was actually received'
        ))
    
    # Add refund eligibility flag
    if 'refund_eligible' not in columns:
        op.add_column('verifications', sa.Column(
            'refund_eligible',
            sa.Boolean(),
            server_default='true',
            nullable=False,
            comment='Whether this failure qualifies for refund'
        ))
    
    # Create indexes for analytics queries
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('verifications')]
    
    if 'idx_verifications_sms_received' not in existing_indexes:
        op.create_index(
            'idx_verifications_sms_received',
            'verifications',
            ['user_id', 'sms_received'],
            postgresql_where=sa.text('sms_received = true')
        )
    
    if 'idx_verifications_failure_reason' not in existing_indexes:
        op.create_index(
            'idx_verifications_failure_reason',
            'verifications',
            ['user_id', 'failure_reason'],
            postgresql_where=sa.text('failure_reason IS NOT NULL')
        )
    
    if 'idx_verifications_refund_tracking_v2' not in existing_indexes:
        op.create_index(
            'idx_verifications_refund_tracking_v2',
            'verifications',
            ['user_id', 'refunded', 'created_at']
        )
    
    # Add foreign keys to balance_transactions
    # Note: SQLite doesn't support adding foreign keys to existing tables easily, 
    # but we'll define them for Postgres.
    
    # Check if foreign keys already exist is harder, but we'll try to add them.
    try:
        op.create_foreign_key(
            'fk_verifications_debit_transaction',
            'verifications',
            'balance_transactions',
            ['debit_transaction_id'],
            ['id'],
            ondelete='SET NULL'
        )
    except Exception:
        pass
        
    try:
        op.create_foreign_key(
            'fk_verifications_refund_transaction',
            'verifications',
            'balance_transactions',
            ['refund_transaction_id'],
            ['id'],
            ondelete='SET NULL'
        )
    except Exception:
        pass


def downgrade() -> None:
    """Remove financial tracking and status columns."""
    # Drop foreign keys first
    try:
        op.drop_constraint('fk_verifications_refund_transaction', 'verifications', type_='foreignkey')
    except: pass
    try:
        op.drop_constraint('fk_verifications_debit_transaction', 'verifications', type_='foreignkey')
    except: pass
    
    # Drop indexes
    try:
        op.drop_index('idx_verifications_refund_tracking_v2')
    except: pass
    try:
        op.drop_index('idx_verifications_failure_reason')
    except: pass
    try:
        op.drop_index('idx_verifications_sms_received')
    except: pass
    
    # Drop columns
    op.drop_column('verifications', 'refund_eligible')
    op.drop_column('verifications', 'sms_received')
    op.drop_column('verifications', 'failure_category')
    op.drop_column('verifications', 'failure_reason')
    op.drop_column('verifications', 'refund_transaction_id')
    op.drop_column('verifications', 'debit_transaction_id')