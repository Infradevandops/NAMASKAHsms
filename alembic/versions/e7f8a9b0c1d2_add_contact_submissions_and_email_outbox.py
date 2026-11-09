"""add contact_submissions and email_outbox tables

Revision ID: e7f8a9b0c1d2
Revises: add_user_events_analytics
Create Date: 2026-11-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "e7f8a9b0c1d2"
down_revision = "add_user_events_analytics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contact_submissions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("category", sa.String(50), nullable=False, server_default="support"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("forwarding_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("forwarding_error", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contact_submissions_email", "contact_submissions", ["email"])

    op.create_table(
        "email_outbox",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("email_class", sa.String(50), nullable=False),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("template_key", sa.String(100), nullable=True),
        sa.Column("recipient_email", sa.String(255), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("lease_owner", sa.String(100), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(), nullable=True),
        sa.Column("provider_name", sa.String(50), nullable=True),
        sa.Column("provider_message_id", sa.String(255), nullable=True),
        sa.Column("last_error", sa.String(500), nullable=True),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("terminal_at", sa.DateTime(), nullable=True),
        sa.Column("source_event_id", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_email_outbox_idempotency_key"),
    )
    op.create_index("ix_email_outbox_idempotency_key", "email_outbox", ["idempotency_key"])
    op.create_index("ix_email_outbox_status", "email_outbox", ["status"])
    op.create_index("ix_email_outbox_next_attempt_at", "email_outbox", ["next_attempt_at"])
    op.create_index("ix_email_outbox_source_event_id", "email_outbox", ["source_event_id"])


def downgrade() -> None:
    op.drop_table("email_outbox")
    op.drop_table("contact_submissions")
