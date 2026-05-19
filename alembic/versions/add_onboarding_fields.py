"""add onboarding fields to users

Revision ID: add_onboarding_fields
Revises: tab_enhancements_v1
Create Date: 2026-05-18
"""

import sqlalchemy as sa

from alembic import op

revision = "add_onboarding_fields"
down_revision = "tab_enhancements_v1"
branch_labels = None
depends_on = None


def _column_exists(table, column):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    try:
        columns = [col["name"] for col in inspector.get_columns(table)]
        return column in columns
    except Exception:
        return False


def upgrade():
    if not _column_exists("users", "onboarding_completed"):
        op.add_column(
            "users",
            sa.Column(
                "onboarding_completed",
                sa.Boolean(),
                nullable=False,
                server_default="false",
            ),
        )
    if not _column_exists("users", "onboarding_step"):
        op.add_column(
            "users",
            sa.Column(
                "onboarding_step",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
        )


def downgrade():
    op.drop_column("users", "onboarding_step")
    op.drop_column("users", "onboarding_completed")
