"""Safe add subscription tier columns

Revision ID: safe_add_tiers
Revises: 
Create Date: 2025-12-24

"""

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision = "safe_add_tiers"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Safely add subscription tier columns if they don't exist."""

    bind = op.get_bind()
    inspector = inspect(bind)

    # Get existing columns in users table
    existing_columns = [col["name"] for col in inspector.get_columns("users")]

    # Add subscription_tier if missing
    if "subscription_tier" not in existing_columns:
        op.add_column(
            "users",
            sa.Column(
                "subscription_tier",
                sa.String(20),
                nullable=False,
                server_default="freemium",
            ),
        )
        op.create_index(
            "ix_users_subscription_tier", "users", ["subscription_tier"], unique=False
        )

    # Add tier_upgraded_at if missing
    if "tier_upgraded_at" not in existing_columns:
        op.add_column(
            "users", sa.Column("tier_upgraded_at", sa.DateTime(), nullable=True)
        )

    # Add tier_expires_at if missing
    if "tier_expires_at" not in existing_columns:
        op.add_column(
            "users", sa.Column("tier_expires_at", sa.DateTime(), nullable=True)
        )


def downgrade():
    """Remove subscription tier columns."""
    pass  # Don't remove in production
