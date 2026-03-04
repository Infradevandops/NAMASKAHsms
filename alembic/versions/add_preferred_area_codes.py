"""Add preferred_area_codes to user_preferences

Revision ID: add_preferred_area_codes
Revises: add_user_preferences
Create Date: 2026-01-18
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_preferred_area_codes'
down_revision = 'add_user_preferences'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user_preferences', sa.Column('preferred_area_codes', sa.String(), nullable=True))


def downgrade():
    op.drop_column('user_preferences', 'preferred_area_codes')
