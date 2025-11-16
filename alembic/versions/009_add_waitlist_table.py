"""Add waitlist table

Revision ID: 009_add_waitlist_table
Revises: 008_add_enterprise_features
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '009_add_waitlist_table'
down_revision = '008'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('waitlist',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('is_notified', sa.Boolean(), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_waitlist_email'), 'waitlist', ['email'], unique=True)

def downgrade():
    op.drop_index(op.f('ix_waitlist_email'), table_name='waitlist')
    op.drop_table('waitlist')