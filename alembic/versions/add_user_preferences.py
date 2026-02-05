"""Add language and currency to users

Revision ID: add_user_preferences
Revises: safe_add_tiers
Create Date: 2025-01-09

"""

import sqlalchemy as sa
from sqlalchemy import inspect
from alembic import op


# revision identifiers, used by Alembic.
revision = "add_user_preferences"
down_revision = "safe_add_tiers"
branch_labels = None
depends_on = None
def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = [col["name"] for col in inspector.get_columns("users")]
    if "language" not in existing_columns:
        op.add_column(
            "users",
            sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        )
    if "currency" not in existing_columns:
        op.add_column(
            "users",
            sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        )
def downgrade():
    pass