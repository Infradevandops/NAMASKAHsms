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
    """Add dispute comments, attachments, and timeline tables."""

    # Create dispute_comments table
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

    # Create dispute_attachments table
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

    # Create dispute_timeline table
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
    """Remove dispute comments, attachments, and timeline tables."""
    op.drop_index("ix_dispute_timeline_created_at", "dispute_timeline")
    op.drop_index("ix_dispute_timeline_dispute_id", "dispute_timeline")
    op.drop_table("dispute_timeline")

    op.drop_index("ix_dispute_attachments_uploaded_at", "dispute_attachments")
    op.drop_index("ix_dispute_attachments_dispute_id", "dispute_attachments")
    op.drop_table("dispute_attachments")

    op.drop_index("ix_dispute_comments_created_at", "dispute_comments")
    op.drop_index("ix_dispute_comments_dispute_id", "dispute_comments")
    op.drop_table("dispute_comments")
