"""Add priority and subject to support tickets

Revision ID: add_support_ticket_fields
Revises:
Create Date: 2026-05-17 12:50:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_support_ticket_fields"
down_revision = "f9a8b7c6d5e4"
branch_labels = None
depends_on = None


def upgrade():
    """Add priority and subject columns to support_tickets table."""
    from sqlalchemy import inspect

    conn = op.get_bind()
    inspector = inspect(conn)

    # Check if table exists
    if "support_tickets" not in inspector.get_table_names():
        return

    # Get existing columns
    existing_columns = [col["name"] for col in inspector.get_columns("support_tickets")]

    # Add priority column if it doesn't exist
    if "priority" not in existing_columns:
        op.add_column(
            "support_tickets",
            sa.Column("priority", sa.String(), nullable=False, server_default="medium"),
        )

    # Add subject column if it doesn't exist
    if "subject" not in existing_columns:
        op.add_column(
            "support_tickets",
            sa.Column("subject", sa.String(), nullable=True),
        )

        # Update existing rows to have a subject
        op.execute(
            "UPDATE support_tickets SET subject = 'Support Request' WHERE subject IS NULL"
        )

        # Make subject non-nullable
        op.alter_column("support_tickets", "subject", nullable=False)


def downgrade():
    """Remove priority and subject columns from support_tickets table."""
    from sqlalchemy import inspect

    conn = op.get_bind()
    inspector = inspect(conn)

    # Check if table exists
    if "support_tickets" not in inspector.get_table_names():
        return

    # Get existing columns
    existing_columns = [col["name"] for col in inspector.get_columns("support_tickets")]

    # Drop columns only if they exist
    if "subject" in existing_columns:
        op.drop_column("support_tickets", "subject")
    if "priority" in existing_columns:
        op.drop_column("support_tickets", "priority")
