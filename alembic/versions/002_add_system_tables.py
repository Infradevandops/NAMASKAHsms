"""Add system tables

Revision ID: 002
Revises: 001
Create Date: 2024-10-31 23:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing system tables."""

    # Support tickets table
    op.create_table(
        "support_tickets",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("admin_response", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_support_tickets_status"), "support_tickets", ["status"])
    op.create_index(op.f("ix_support_tickets_user_id"), "support_tickets", ["user_id"])

    # Service status table
    op.create_table(
        "service_status",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("service_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("success_rate", sa.Float(), nullable=False),
        sa.Column("last_checked", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_service_status_service_name"), "service_status", ["service_name"]
    )
    op.create_index(
        op.f("ix_service_status_last_checked"), "service_status", ["last_checked"]
    )


def downgrade() -> None:
    """Drop system tables."""
    op.drop_table("service_status")
    op.drop_table("support_tickets")
