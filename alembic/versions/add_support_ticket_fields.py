"""Add priority and subject to support tickets

Revision ID: add_support_ticket_fields
Revises:
Create Date: 2026-05-17 12:50:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_support_ticket_fields"
down_revision = None  # Update this to your latest migration
branch_labels = None
depends_on = None


def upgrade():
    """Add priority and subject columns to support_tickets table."""
    # Add priority column with default value
    op.add_column(
        "support_tickets",
        sa.Column("priority", sa.String(), nullable=False, server_default="medium"),
    )

    # Add subject column with default value for existing rows
    op.add_column(
        "support_tickets",
        sa.Column("subject", sa.String(), nullable=True),  # Nullable first
    )

    # Update existing rows to have a subject
    op.execute(
        "UPDATE support_tickets SET subject = 'Support Request' WHERE subject IS NULL"
    )

    # Make subject non-nullable
    op.alter_column("support_tickets", "subject", nullable=False)


def downgrade():
    """Remove priority and subject columns from support_tickets table."""
    op.drop_column("support_tickets", "subject")
    op.drop_column("support_tickets", "priority")
