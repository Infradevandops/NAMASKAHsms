"""Add 5SIM fields to verification table

Revision ID: 013_add_5sim_fields
Revises: 012_add_affiliate_system
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '013_add_5sim_fields'
down_revision = '012_add_affiliate_system'
branch_labels = None
depends_on = None


def upgrade():
    """Add 5SIM specific fields to verification table."""
    # Add provider field (5sim, textverified, etc.)
    op.add_column('verifications', sa.Column('provider', sa.String(50), default='5sim'))
    
    # Add operator field (any, mts, beeline, etc.)
    op.add_column('verifications', sa.Column('operator', sa.String(50), nullable=True))
    
    # Add pricing tier (standard, premium, bulk)
    op.add_column('verifications', sa.Column('pricing_tier', sa.String(20), default='standard'))
    
    # Add 5SIM activation ID (integer from 5SIM API)
    op.add_column('verifications', sa.Column('activation_id', sa.BigInteger(), nullable=True))
    
    # Add SMS text storage
    op.add_column('verifications', sa.Column('sms_text', sa.Text(), nullable=True))
    
    # Add extracted SMS code
    op.add_column('verifications', sa.Column('sms_code', sa.String(20), nullable=True))
    
    # Add SMS received timestamp
    op.add_column('verifications', sa.Column('sms_received_at', sa.DateTime(), nullable=True))
    
    # Add indexes for performance
    op.create_index('idx_verifications_activation_id', 'verifications', ['activation_id'])
    op.create_index('idx_verifications_provider', 'verifications', ['provider'])
    op.create_index('idx_verifications_status', 'verifications', ['status'])


def downgrade():
    """Remove 5SIM fields."""
    # Drop indexes first
    op.drop_index('idx_verifications_status', 'verifications')
    op.drop_index('idx_verifications_provider', 'verifications')
    op.drop_index('idx_verifications_activation_id', 'verifications')
    
    # Drop columns
    op.drop_column('verifications', 'sms_received_at')
    op.drop_column('verifications', 'sms_code')
    op.drop_column('verifications', 'sms_text')
    op.drop_column('verifications', 'activation_id')
    op.drop_column('verifications', 'pricing_tier')
    op.drop_column('verifications', 'operator')
    op.drop_column('verifications', 'provider')