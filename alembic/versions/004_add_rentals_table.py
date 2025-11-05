"""Add rentals table

Revision ID: 004
Revises: 003
Create Date: 2025-11-04 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create rentals table
    op.create_table('rentals',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('(now())')),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('user_id', sa.String(36), nullable=False, index=True),
        sa.Column('phone_number', sa.String(20), nullable=False),
        sa.Column('service_name', sa.String(50), nullable=False),
        sa.Column('country_code', sa.String(3), nullable=False),
        sa.Column('provider', sa.String(20), default='5sim'),
        sa.Column('activation_id', sa.String(50), nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('cost', sa.Numeric(10, 4), nullable=False),
        sa.Column('duration_hours', sa.Integer, default=24)
    )

def downgrade() -> None:
    op.drop_table('rentals')