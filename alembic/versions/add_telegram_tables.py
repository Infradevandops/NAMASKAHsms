"""Add Telegram integration tables

Revision ID: add_telegram_tables
Revises: add_mfa_fields
Create Date: 2026-05-07

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_telegram_tables"
down_revision = "add_mfa_fields"
branch_labels = None
depends_on = None


def upgrade():
    # Create telegram_connections table
    op.create_table(
        "telegram_connections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(255), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "connected_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("last_message_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chat_id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        "ix_telegram_connections_user_id", "telegram_connections", ["user_id"]
    )
    op.create_index(
        "ix_telegram_connections_chat_id", "telegram_connections", ["chat_id"]
    )
    op.create_index(
        "ix_telegram_connections_active", "telegram_connections", ["active"]
    )

    # Create telegram_forwarding_rules table
    op.create_table(
        "telegram_forwarding_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("forward_all", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("service_filter", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("country_filter", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        "ix_telegram_forwarding_rules_user_id", "telegram_forwarding_rules", ["user_id"]
    )


def downgrade():
    op.drop_index(
        "ix_telegram_forwarding_rules_user_id", table_name="telegram_forwarding_rules"
    )
    op.drop_table("telegram_forwarding_rules")

    op.drop_index("ix_telegram_connections_active", table_name="telegram_connections")
    op.drop_index("ix_telegram_connections_chat_id", table_name="telegram_connections")
    op.drop_index("ix_telegram_connections_user_id", table_name="telegram_connections")
    op.drop_table("telegram_connections")
