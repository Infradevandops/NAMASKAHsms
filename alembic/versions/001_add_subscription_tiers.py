"""Add subscription tiers and API key enhancements

Revision ID: 001_add_subscription_tiers
Revises: 
Create Date: 2025-12-07 20:57:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '001_add_subscription_tiers'
down_revision = None  # Update this to previous migration if exists
branch_labels = None
depends_on = None


def upgrade():
    """Add subscription tier support."""
    
    # Add tier fields to users table
    op.add_column('users', sa.Column('subscription_tier', sa.String(20), nullable=False, server_default='freemium'))
    op.add_column('users', sa.Column('tier_upgraded_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('tier_expires_at', sa.DateTime(), nullable=True))
    op.create_index('ix_users_subscription_tier', 'users', ['subscription_tier'])
    
    # Create subscription_tiers table
    op.create_table(
        'subscription_tiers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tier', sa.String(20), unique=True, nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('price_monthly', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('payment_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('has_api_access', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('has_area_code_selection', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('has_isp_filtering', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('api_key_limit', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('daily_verification_limit', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('monthly_verification_limit', sa.Integer(), nullable=False, server_default='3000'),
        sa.Column('country_limit', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('sms_retention_days', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('support_level', sa.String(20), nullable=False, server_default='community'),
        sa.Column('features', sa.JSON(), nullable=True),
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('rate_limit_per_hour', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('ix_subscription_tiers_tier', 'subscription_tiers', ['tier'])
    
    # Enhance api_keys table
    op.add_column('api_keys', sa.Column('key_preview', sa.String(20), nullable=True))
    op.add_column('api_keys', sa.Column('expires_at', sa.DateTime(), nullable=True))
    
    # Rename key to key_hash for security (if column exists)
    try:
        op.alter_column('api_keys', 'key', new_column_name='key_hash')
    except:
        # Column might not exist or already renamed
        pass
    
    # Seed subscription tiers
    op.execute("""
        INSERT INTO subscription_tiers (id, tier, name, description, price_monthly, payment_required,
                                        has_api_access, has_area_code_selection, has_isp_filtering,
                                        api_key_limit, daily_verification_limit, monthly_verification_limit,
                                        country_limit, sms_retention_days, support_level,
                                        rate_limit_per_minute, rate_limit_per_hour, features)
        VALUES
        (gen_random_uuid(), 'freemium', 'Freemium', 'Free tier with basic features', 0, false,
         false, false, false, 0, 100, 3000, 5, 1, 'community', 10, 100,
         '{"webhooks": false, "priority_routing": false, "custom_branding": false}'),
        
        (gen_random_uuid(), 'starter', 'Starter', 'Developer tier with API access and area code selection', 900, true,
         true, true, false, 5, 1000, 30000, 20, 7, 'email', 50, 1000,
         '{"webhooks": true, "priority_routing": false, "custom_branding": false}'),
        
        (gen_random_uuid(), 'turbo', 'Turbo', 'Premium tier with ISP filtering and unlimited API keys', 1399, true,
         true, true, true, -1, 10000, 300000, -1, 30, 'priority', 200, 10000,
         '{"webhooks": true, "priority_routing": true, "custom_branding": true}')
    """)


def downgrade():
    """Remove subscription tier support."""
    
    # Drop tier fields from users
    op.drop_index('ix_users_subscription_tier', 'users')
    op.drop_column('users', 'subscription_tier')
    op.drop_column('users', 'tier_upgraded_at')
    op.drop_column('users', 'tier_expires_at')
    
    # Drop subscription_tiers table
    op.drop_index('ix_subscription_tiers_tier', 'subscription_tiers')
    op.drop_table('subscription_tiers')
    
    # Revert api_keys changes
    op.drop_column('api_keys', 'key_preview')
    op.drop_column('api_keys', 'expires_at')
    try:
        op.alter_column('api_keys', 'key_hash', new_column_name='key')
    except:
        pass
