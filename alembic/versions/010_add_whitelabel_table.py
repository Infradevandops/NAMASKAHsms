"""Add whitelabel table

Revision ID: 010_add_whitelabel_table
Revises: 009_add_waitlist_table
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '010_add_whitelabel_table'
down_revision = '009_add_waitlist_table'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('whitelabel_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('company_name', sa.String(length=100), nullable=False),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('primary_color', sa.String(length=7), nullable=True),
        sa.Column('secondary_color', sa.String(length=7), nullable=True),
        sa.Column('custom_css', sa.Text(), nullable=True),
        sa.Column('api_subdomain', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('features', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_whitelabel_configs_domain'), 'whitelabel_configs', ['domain'], unique=True)

def downgrade():
    op.drop_index(op.f('ix_whitelabel_configs_domain'), table_name='whitelabel_configs')
    op.drop_table('whitelabel_configs')