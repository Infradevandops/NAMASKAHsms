"""Add preferred_area_codes to user_preferences

Revision ID: add_preferred_area_codes
Revises: add_user_preferences
Create Date: 2026-01-18
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_preferred_area_codes'
down_revision = '003_payment_idempotency'
branch_labels = None
depends_on = None


def _column_exists(table, column):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns(table)]
    return column in columns
 
 
def _table_exists(table):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    return table in tables
 
 
def upgrade():
    if not _table_exists("user_preferences"):
        return
    if not _column_exists('user_preferences', 'preferred_area_codes'):
        op.add_column('user_preferences', sa.Column('preferred_area_codes', sa.String(), nullable=True))


def downgrade():
    op.drop_column('user_preferences', 'preferred_area_codes')
