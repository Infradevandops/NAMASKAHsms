"""add tab enhancements

Revision ID: tab_enhancements_v1
Revises: a6e1cc3527b6
Create Date: 2026-05-17
"""

from datetime import datetime

import sqlalchemy as sa

from alembic import op

revision = "tab_enhancements_v1"
down_revision = "a6e1cc3527b6"
branch_labels = None
depends_on = None


def _column_exists(table, column):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    try:
        columns = [col["name"] for col in inspector.get_columns(table)]
        return column in columns
    except:
        return False


def _table_exists(table):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table in inspector.get_table_names()


def upgrade():
    # Add support_tickets enhancements
    if not _column_exists("support_tickets", "priority"):
        op.add_column(
            "support_tickets",
            sa.Column("priority", sa.String(), nullable=False, server_default="medium"),
        )

    if not _column_exists("support_tickets", "subject"):
        op.add_column(
            "support_tickets",
            sa.Column(
                "subject", sa.String(), nullable=False, server_default="Support Request"
            ),
        )


def downgrade():
    # Drop support_tickets columns
    if _column_exists("support_tickets", "subject"):
        op.drop_column("support_tickets", "subject")

    if _column_exists("support_tickets", "priority"):
        op.drop_column("support_tickets", "priority")
