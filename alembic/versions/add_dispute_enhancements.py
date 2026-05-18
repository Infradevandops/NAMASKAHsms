"""Add dispute comments, attachments, and timeline tables

Revision ID: add_dispute_enhancements
Revises: add_support_ticket_fields
Create Date: 2026-05-17 13:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_dispute_enhancements"
down_revision = "add_support_ticket_fields"
branch_labels = None
depends_on = None


def upgrade():
    """Add disputes table and related tables."""
    from sqlalchemy import inspect
    from sqlalchemy.engine import reflection

    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    # Create disputes table first (parent table)
    if "disputes" not in existing_tables:
        op.create_table(
            "disputes",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("transaction_id", sa.String(), nullable=True),
            sa.Column("payment_log_id", sa.String(), nullable=False),
            sa.Column("amount", sa.Float(), nullable=False),
            sa.Column("reason_code", sa.String(), nullable=False),
            sa.Column("reason_description", sa.String(), nullable=False),
            sa.Column("dispute_date", sa.DateTime(), nullable=False),
            sa.Column("status", sa.String(), nullable=False, server_default="opened"),
            sa.Column("resolution", sa.String(), nullable=True),
            sa.Column("resolution_date", sa.DateTime(), nullable=True),
            sa.Column("resolution_notes", sa.String(), nullable=True),
            sa.Column(
                "balance_reversed", sa.Boolean(), nullable=False, server_default="false"
            ),
            sa.Column("reversal_amount", sa.Float(), nullable=True),
            sa.Column("reversal_at", sa.DateTime(), nullable=True),
            sa.Column("evidence_notes", sa.String(), nullable=True),
            sa.Column("evidence_files", sa.String(), nullable=True),
            sa.Column("assigned_to", sa.String(), nullable=True),
            sa.Column("assigned_at", sa.DateTime(), nullable=True),
            sa.Column("last_updated_by", sa.String(), nullable=True),
            sa.Column("last_updated_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["transaction_id"], ["sms_transactions.id"]),
            sa.ForeignKeyConstraint(["payment_log_id"], ["payment_logs.id"]),
        )
        op.create_index("ix_disputes_user_id", "disputes", ["user_id"])
        op.create_index("ix_disputes_transaction_id", "disputes", ["transaction_id"])
        op.create_index("ix_disputes_payment_log_id", "disputes", ["payment_log_id"])
        op.create_index("ix_disputes_reason_code", "disputes", ["reason_code"])
        op.create_index("ix_disputes_dispute_date", "disputes", ["dispute_date"])
        op.create_index("ix_disputes_status", "disputes", ["status"])
        op.create_index("ix_disputes_created_at", "disputes", ["created_at"])

    # Create dispute_comments table only if it doesn't exist
    if "dispute_comments" not in existing_tables:
        op.create_table(
            "dispute_comments",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("dispute_id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("content", sa.String(), nullable=False),
            sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["dispute_id"], ["disputes.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        )
        op.create_index(
            "ix_dispute_comments_dispute_id", "dispute_comments", ["dispute_id"]
        )
        op.create_index(
            "ix_dispute_comments_created_at", "dispute_comments", ["created_at"]
        )

    # Create dispute_attachments table only if it doesn't exist
    if "dispute_attachments" not in existing_tables:
        op.create_table(
            "dispute_attachments",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("dispute_id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("filename", sa.String(), nullable=False),
            sa.Column("file_path", sa.String(), nullable=False),
            sa.Column("file_size", sa.Integer(), nullable=False),
            sa.Column("content_type", sa.String(), nullable=False),
            sa.Column("uploaded_at", sa.DateTime(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["dispute_id"], ["disputes.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        )
        op.create_index(
            "ix_dispute_attachments_dispute_id", "dispute_attachments", ["dispute_id"]
        )
        op.create_index(
            "ix_dispute_attachments_uploaded_at", "dispute_attachments", ["uploaded_at"]
        )

    # Create dispute_timeline table only if it doesn't exist
    if "dispute_timeline" not in existing_tables:
        op.create_table(
            "dispute_timeline",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("dispute_id", sa.String(), nullable=False),
            sa.Column("event_type", sa.String(), nullable=False),
            sa.Column("event_description", sa.String(), nullable=False),
            sa.Column("actor_id", sa.String(), nullable=True),
            sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("event_metadata", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["dispute_id"], ["disputes.id"]),
        )
        op.create_index(
            "ix_dispute_timeline_dispute_id", "dispute_timeline", ["dispute_id"]
        )
        op.create_index(
            "ix_dispute_timeline_created_at", "dispute_timeline", ["created_at"]
        )


def downgrade():
    """Remove disputes table and related tables."""
    from sqlalchemy import inspect

    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    # Drop child tables first (foreign key constraints)
    if "dispute_timeline" in existing_tables:
        op.drop_index("ix_dispute_timeline_created_at", "dispute_timeline")
        op.drop_index("ix_dispute_timeline_dispute_id", "dispute_timeline")
        op.drop_table("dispute_timeline")

    if "dispute_attachments" in existing_tables:
        op.drop_index("ix_dispute_attachments_uploaded_at", "dispute_attachments")
        op.drop_index("ix_dispute_attachments_dispute_id", "dispute_attachments")
        op.drop_table("dispute_attachments")

    if "dispute_comments" in existing_tables:
        op.drop_index("ix_dispute_comments_created_at", "dispute_comments")
        op.drop_index("ix_dispute_comments_dispute_id", "dispute_comments")
        op.drop_table("dispute_comments")

    # Drop parent table last
    if "disputes" in existing_tables:
        op.drop_index("ix_disputes_created_at", "disputes")
        op.drop_index("ix_disputes_status", "disputes")
        op.drop_index("ix_disputes_dispute_date", "disputes")
        op.drop_index("ix_disputes_reason_code", "disputes")
        op.drop_index("ix_disputes_payment_log_id", "disputes")
        op.drop_index("ix_disputes_transaction_id", "disputes")
        op.drop_index("ix_disputes_user_id", "disputes")
        op.drop_table("disputes")
