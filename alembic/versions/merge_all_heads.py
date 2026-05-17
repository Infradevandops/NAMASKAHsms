"""Merge migration heads into single lineage.

Revision ID: merge_all_heads
Revises: add_cancellation_fields, add_whitelabel_custom_tables
Create Date: 2026-05-17 12:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "merge_all_heads"
down_revision = ("add_cancellation_fields", "add_whitelabel_custom_tables")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
