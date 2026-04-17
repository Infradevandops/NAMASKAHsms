"""Add refund tracking fields to verifications table

Revision ID: add_refund_fields
Revises: 
Create Date: 2026-04-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_refund_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add refund tracking fields to verifications table."""
    
    # Add refund tracking fields
    op.add_column('verifications', sa.Column('refunded', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('verifications', sa.Column('refund_amount', sa.Float(), nullable=True))
    op.add_column('verifications', sa.Column('refund_reason', sa.String(), nullable=True))
    op.add_column('verifications', sa.Column('refund_transaction_id', sa.String(), nullable=True))
    op.add_column('verifications', sa.Column('refunded_at', sa.DateTime(), nullable=True))
    
    # Create index for refunded field (for efficient queries)
    op.create_index('ix_verifications_refunded', 'verifications', ['refunded'])
    
    print("✅ Added refund tracking fields to verifications table")


def downgrade():
    """Remove refund tracking fields from verifications table."""
    
    # Drop index
    op.drop_index('ix_verifications_refunded', table_name='verifications')
    
    # Drop columns
    op.drop_column('verifications', 'refunded_at')
    op.drop_column('verifications', 'refund_transaction_id')
    op.drop_column('verifications', 'refund_reason')
    op.drop_column('verifications', 'refund_amount')
    op.drop_column('verifications', 'refunded')
    
    print("✅ Removed refund tracking fields from verifications table")
