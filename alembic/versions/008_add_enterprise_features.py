"""Add enterprise features

Revision ID: 008
Revises: 007
Create Date: 2025-01-01 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

revision = "008"
down_revision = "007_add_kyc_system"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create API keys table
    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("(now())")),
        sa.Column("updated_at", sa.DateTime),
        sa.Column("user_id", sa.String(36), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("prefix", sa.String(10), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("last_used", sa.DateTime),
        sa.Column("expires_at", sa.DateTime),
    )

    # Create audit logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("(now())")),
        sa.Column("updated_at", sa.DateTime),
        sa.Column("user_id", sa.String(36), index=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(36)),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.Text),
        sa.Column("details", sa.JSON),
    )

    # Add MFA fields to users table
    op.add_column("users", sa.Column("mfa_secret", sa.String(32)))
    op.add_column("users", sa.Column("mfa_enabled", sa.Boolean, default=False))


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("api_keys")
    op.drop_column("users", "mfa_enabled")
    op.drop_column("users", "mfa_secret")
