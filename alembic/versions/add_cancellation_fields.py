"""Add cancelled_at and cancelled_by to verifications

Revision ID: add_cancellation_fields
Revises:
Create Date: 2026-05-17

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_cancellation_fields"
down_revision = None  # Update this to your latest migration
branch_labels = None
depends_on = None


def upgrade():
    """Add cancellation tracking fields to verifications table."""

    # Add cancelled_at column
    op.add_column(
        "verifications",
        sa.Column(
            "cancelled_at",
            sa.DateTime(),
            nullable=True,
            comment="When verification was cancelled",
        ),
    )

    # Add cancelled_by column
    op.add_column(
        "verifications",
        sa.Column(
            "cancelled_by",
            sa.String(length=50),
            nullable=True,
            comment="Who cancelled: user, system, admin",
        ),
    )


def downgrade():
    """Remove cancellation tracking fields."""

    op.drop_column("verifications", "cancelled_by")
    op.drop_column("verifications", "cancelled_at")
