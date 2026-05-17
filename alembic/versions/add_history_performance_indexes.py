"""Add history performance indexes

Revision ID: f9a8b7c6d5e4
Revises:
Create Date: 2026-05-17 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "f9a8b7c6d5e4"
down_revision = None  # Update this to point to your latest migration
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes for history queries."""
    # Index for sorting by created_at (most common query)
    op.create_index(
        "idx_verifications_created_at_desc",
        "verifications",
        [sa.text("created_at DESC")],
        unique=False,
    )

    # Composite index for user + status + created_at (filtered queries)
    op.create_index(
        "idx_verifications_user_status_created",
        "verifications",
        ["user_id", "status", sa.text("created_at DESC")],
        unique=False,
    )

    # Index for phone number searches (LIKE queries)
    op.create_index(
        "idx_verifications_phone_number",
        "verifications",
        ["phone_number"],
        unique=False,
    )

    # Index for SMS code lookups
    op.create_index(
        "idx_verifications_sms_code", "verifications", ["sms_code"], unique=False
    )


def downgrade():
    """Remove performance indexes."""
    op.drop_index("idx_verifications_sms_code", table_name="verifications")
    op.drop_index("idx_verifications_phone_number", table_name="verifications")
    op.drop_index("idx_verifications_user_status_created", table_name="verifications")
    op.drop_index("idx_verifications_created_at_desc", table_name="verifications")
