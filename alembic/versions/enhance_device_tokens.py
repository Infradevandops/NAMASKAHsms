"""Enhance device_tokens for web push notifications

Revision ID: enhance_device_tokens
Revises: add_telegram_tables
Create Date: 2026-05-07

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "enhance_device_tokens"
down_revision = "add_telegram_tables"
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns for web push support
    op.add_column(
        "device_tokens", sa.Column("device_type", sa.String(50), nullable=True)
    )
    op.add_column(
        "device_tokens", sa.Column("last_used_at", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "device_tokens", sa.Column("expires_at", sa.DateTime(), nullable=True)
    )
    op.add_column(
        "device_tokens",
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
    )

    # Rename device_token to token for consistency
    op.alter_column(
        "device_tokens",
        "device_token",
        new_column_name="token",
        existing_type=sa.String(500),
    )

    # Update platform column to support 'web'
    # Existing values: 'ios', 'android'
    # New value: 'web'

    # Add index on active column
    op.create_index("ix_device_tokens_active", "device_tokens", ["active"])

    # Migrate existing is_active to active
    op.execute(
        "UPDATE device_tokens SET active = is_active WHERE is_active IS NOT NULL"
    )

    # Drop old is_active column
    op.drop_column("device_tokens", "is_active")


def downgrade():
    # Restore is_active column
    op.add_column(
        "device_tokens",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.execute("UPDATE device_tokens SET is_active = active WHERE active IS NOT NULL")

    # Drop new columns
    op.drop_index("ix_device_tokens_active", table_name="device_tokens")
    op.drop_column("device_tokens", "active")
    op.drop_column("device_tokens", "expires_at")
    op.drop_column("device_tokens", "last_used_at")
    op.drop_column("device_tokens", "device_type")

    # Rename token back to device_token
    op.alter_column(
        "device_tokens",
        "token",
        new_column_name="device_token",
        existing_type=sa.String(500),
    )
