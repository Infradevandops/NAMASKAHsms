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
    return bind.execute(sa.text(
        "SELECT 1 FROM information_schema.columns WHERE table_name=:t AND column_name=:c"
    ).bindparams(t=table, c=column)).fetchone() is not None


def upgrade():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT 1 FROM information_schema.tables WHERE table_name='user_preferences'")).fetchone() is None:
        return
    if not _column_exists('user_preferences', 'preferred_area_codes'):
        op.add_column('user_preferences', sa.Column('preferred_area_codes', sa.String(), nullable=True))


def downgrade():
    op.drop_column('user_preferences', 'preferred_area_codes')
