"""Initial schema migration

Revision ID: 001
Revises:
Create Date: 2024-01-20 10:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables from existing schema."""

    # Users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column(
            "password_hash", sa.String(length=255), nullable=True
        ),  # Nullable for OAuth
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=True),
        sa.Column("email_verified", sa.Boolean(), nullable=True),
        sa.Column("credits", sa.Float(), nullable=True),
        sa.Column("free_verifications", sa.Float(), nullable=True),
        sa.Column("verification_token", sa.String(length=255), nullable=True),
        sa.Column("reset_token", sa.String(length=255), nullable=True),
        sa.Column("reset_token_expires", sa.DateTime(timezone=True), nullable=True),
        sa.Column("referral_code", sa.String(length=50), nullable=True),
        sa.Column("referred_by", sa.String(length=255), nullable=True),
        sa.Column("referral_earnings", sa.Float(), nullable=True),
        # Google OAuth fields
        sa.Column("google_id", sa.String(255), nullable=True),
        sa.Column("provider", sa.String(50), nullable=False, server_default="email"),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(
        op.f("ix_users_referral_code"), "users", ["referral_code"], unique=True
    )
    op.create_index(op.f("ix_users_google_id"), "users", ["google_id"])
    op.create_index(op.f("ix_users_provider"), "users", ["provider"])

    # API Keys table
    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("last_used", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_api_keys_key"), "api_keys", ["key"], unique=True)

    # Verifications table
    op.create_table(
        "verifications",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("service_name", sa.String(length=100), nullable=False),
        sa.Column("phone_number", sa.String(length=20), nullable=True),
        sa.Column("capability", sa.String(length=10), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("verification_code", sa.String(length=20), nullable=True),
        sa.Column("cost", sa.Float(), nullable=False),
        sa.Column("call_duration", sa.Float(), nullable=True),
        sa.Column("transcription", sa.String(), nullable=True),
        sa.Column("audio_url", sa.String(), nullable=True),
        sa.Column("requested_carrier", sa.String(length=50), nullable=True),
        sa.Column("requested_area_code", sa.String(length=10), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_verifications_service_name"), "verifications", ["service_name"]
    )
    op.create_index(op.f("ix_verifications_status"), "verifications", ["status"])

    # Transactions table
    op.create_table(
        "transactions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transactions_user_id"), "transactions", ["user_id"])
    op.create_index(op.f("ix_transactions_type"), "transactions", ["type"])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("transactions")
    op.drop_table("verifications")
    op.drop_table("api_keys")
    op.drop_table("users")
