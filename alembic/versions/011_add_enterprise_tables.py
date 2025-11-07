"""Add enterprise tables

Revision ID: 011_add_enterprise_tables
Revises: 010_add_whitelabel_table
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '011_add_enterprise_tables'
down_revision = '010_add_whitelabel_table'
branch_labels = None
depends_on = None

def upgrade():
    # Create enterprise_tiers table
    op.create_table('enterprise_tiers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('min_monthly_spend', sa.Float(), nullable=False),
        sa.Column('sla_uptime', sa.Float(), nullable=True),
        sa.Column('max_response_time', sa.Integer(), nullable=True),
        sa.Column('priority_support', sa.Boolean(), nullable=True),
        sa.Column('dedicated_manager', sa.Boolean(), nullable=True),
        sa.Column('custom_rates', sa.JSON(), nullable=True),
        sa.Column('features', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_enterprise_tiers_name'), 'enterprise_tiers', ['name'], unique=True)
    
    # Create enterprise_accounts table
    op.create_table('enterprise_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tier_id', sa.Integer(), nullable=False),
        sa.Column('account_manager_email', sa.String(length=255), nullable=True),
        sa.Column('monthly_spend', sa.Float(), nullable=True),
        sa.Column('sla_credits', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tier_id'], ['enterprise_tiers.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('enterprise_accounts')
    op.drop_index(op.f('ix_enterprise_tiers_name'), table_name='enterprise_tiers')
    op.drop_table('enterprise_tiers')