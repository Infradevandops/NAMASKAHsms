"""add terms_accepted to users

Revision ID: add_terms_accepted
Revises: e9af649b2601
Create Date: 2026-05-03
"""

import sqlalchemy as sa

from alembic import op

revision = "add_terms_accepted"
down_revision = "8dc0a617c07f"
branch_labels = None
depends_on = None


def _column_exists(table, column):
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :table AND column_name = :column"
        ),
        {"table": table, "column": column},
    )
    return result.fetchone() is not None


def upgrade():
    if not _column_exists("users", "terms_accepted"):
        op.add_column(
            "users",
            sa.Column(
                "terms_accepted",
                sa.Boolean(),
                nullable=False,
                server_default="false",
            ),
        )
    if not _column_exists("users", "terms_accepted_at"):
        op.add_column(
            "users",
            sa.Column("terms_accepted_at", sa.DateTime(), nullable=True),
        )


def downgrade():
    op.drop_column("users", "terms_accepted_at")
    op.drop_column("users", "terms_accepted")
