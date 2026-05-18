"""add tab enhancements

Revision ID: tab_enhancements_v1
Revises: a6e1cc3527b6
Create Date: 2026-05-17
"""

from datetime import datetime

import sqlalchemy as sa

from alembic import op

revision = "tab_enhancements_v1"
down_revision = "a6e1cc3527b6"
branch_labels = None
depends_on = None


def _column_exists(table, column):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    try:
        columns = [col["name"] for col in inspector.get_columns(table)]
        return column in columns
    except:
        return False


def _table_exists(table):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table in inspector.get_table_names()


def upgrade():
    # Add support_tickets enhancements
    if not _column_exists("support_tickets", "priority"):
        op.add_column(
            "support_tickets",
            sa.Column("priority", sa.String(), nullable=False, server_default="medium"),
        )

    if not _column_exists("support_tickets", "subject"):
        op.add_column(
            "support_tickets",
            sa.Column(
                "subject", sa.String(), nullable=False, server_default="Support Request"
            ),
        )

    # Create dispute_comments table
    if not _table_exists("dispute_comments"):
        op.create_table(
            "dispute_comments",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("dispute_id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("content", sa.String(), nullable=False),
            sa.Column("is_admin", sa.Boolean(), default=False),
            sa.Column(
                "created_at", sa.DateTime(), nullable=False, default=datetime.utcnow
            ),
            sa.Column(
                "updated_at", sa.DateTime(), nullable=False, default=datetime.utcnow
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["dispute_id"], ["disputes.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )
        op.create_index(
            "ix_dispute_comments_dispute_id", "dispute_comments", ["dispute_id"]
        )
        op.create_index(
            "ix_dispute_comments_created_at", "dispute_comments", ["created_at"]
        )

    # Create dispute_attachments table
    if not _table_exists("dispute_attachments"):
        op.create_table(
            "dispute_attachments",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("dispute_id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("filename", sa.String(), nullable=False),
            sa.Column("file_path", sa.String(), nullable=False),
            sa.Column("file_size", sa.Integer(), nullable=False),
            sa.Column("content_type", sa.String(), nullable=False),
            sa.Column(
                "uploaded_at", sa.DateTime(), nullable=False, default=datetime.utcnow
            ),
            sa.Column(
                "created_at", sa.DateTime(), nullable=False, default=datetime.utcnow
            ),
            sa.Column(
                "updated_at", sa.DateTime(), nullable=False, default=datetime.utcnow
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["dispute_id"], ["disputes.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )
        op.create_index(
            "ix_dispute_attachments_dispute_id", "dispute_attachments", ["dispute_id"]
        )
        op.create_index(
            "ix_dispute_attachments_uploaded_at", "dispute_attachments", ["uploaded_at"]
        )

    # Create dispute_timeline table
    if not _table_exists("dispute_timeline"):
        op.create_table(
            "dispute_timeline",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("dispute_id", sa.String(), nullable=False),
            sa.Column("event_type", sa.String(), nullable=False),
            sa.Column("event_description", sa.String(), nullable=False),
            sa.Column("actor_id", sa.String()),
            sa.Column("is_admin", sa.Boolean(), default=False),
            sa.Column("event_metadata", sa.String()),  # JSON
            sa.Column(
                "created_at", sa.DateTime(), nullable=False, default=datetime.utcnow
            ),
            sa.Column(
                "updated_at", sa.DateTime(), nullable=False, default=datetime.utcnow
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["dispute_id"], ["disputes.id"], ondelete="CASCADE"
            ),
        )
        op.create_index(
            "ix_dispute_timeline_dispute_id", "dispute_timeline", ["dispute_id"]
        )
        op.create_index(
            "ix_dispute_timeline_created_at", "dispute_timeline", ["created_at"]
        )


def downgrade():
    # Drop dispute tables
    if _table_exists("dispute_timeline"):
        op.drop_index("ix_dispute_timeline_created_at", "dispute_timeline")
        op.drop_index("ix_dispute_timeline_dispute_id", "dispute_timeline")
        op.drop_table("dispute_timeline")

    if _table_exists("dispute_attachments"):
        op.drop_index("ix_dispute_attachments_uploaded_at", "dispute_attachments")
        op.drop_index("ix_dispute_attachments_dispute_id", "dispute_attachments")
        op.drop_table("dispute_attachments")

    if _table_exists("dispute_comments"):
        op.drop_index("ix_dispute_comments_created_at", "dispute_comments")
        op.drop_index("ix_dispute_comments_dispute_id", "dispute_comments")
        op.drop_table("dispute_comments")

    # Drop support_tickets columns
    if _column_exists("support_tickets", "subject"):
        op.drop_column("support_tickets", "subject")

    if _column_exists("support_tickets", "priority"):
        op.drop_column("support_tickets", "priority")
