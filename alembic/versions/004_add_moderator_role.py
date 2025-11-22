"""Add moderator role to users.

Revision ID: 004_add_moderator_role
Revises: 003_session_management
Create Date: 2025-11-21 22:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '004_add_moderator_role'
down_revision = '003_session_management'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('users', sa.Column('is_moderator', sa.Boolean(), nullable=True, server_default='0'))

def downgrade():
    op.drop_column('users', 'is_moderator')
