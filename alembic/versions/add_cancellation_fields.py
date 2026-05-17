"""Add cancelled_at and cancelled_by to verifications

Revision ID: add_cancellation_fields
Revises:
Create Date: 2026-05-17

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_cancellation_fields"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add cancellation tracking fields to verifications table."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns("verifications")]

    if "cancelled_at" not in cols:
        op.add_column(
            "verifications",
            sa.Column(
                "cancelled_at",
                sa.DateTime(),
                nullable=True,
                comment="When verification was cancelled",
            ),
        )

    if "cancelled_by" not in cols:
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
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns("verifications")]

    if "cancelled_by" in cols:
        op.drop_column("verifications", "cancelled_by")
    if "cancelled_at" in cols:
        op.drop_column("verifications", "cancelled_at")
