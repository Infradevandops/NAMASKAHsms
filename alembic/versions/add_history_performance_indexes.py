"""Add history performance indexes

Revision ID: f9a8b7c6d5e4
Revises:
Create Date: 2026-05-17 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "f9a8b7c6d5e4"
down_revision = "merge_all_heads"
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes for history queries."""
    conn = op.get_bind()

    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_verifications_created_at_desc ON verifications (created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_verifications_user_status_created ON verifications (user_id, status, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_verifications_phone_number ON verifications (phone_number)",
        "CREATE INDEX IF NOT EXISTS idx_verifications_sms_code ON verifications (sms_code)",
    ]
    for sql in indexes:
        conn.execute(sa.text(sql))


def downgrade():
    """Remove performance indexes."""
    op.drop_index("idx_verifications_sms_code", table_name="verifications")
    op.drop_index("idx_verifications_phone_number", table_name="verifications")
    op.drop_index("idx_verifications_user_status_created", table_name="verifications")
    op.drop_index("idx_verifications_created_at_desc", table_name="verifications")
