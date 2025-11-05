"""Add country field to verification

Revision ID: 003
Revises: 002
Create Date: 2024-12-01 12:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    # Add country column to verifications table
    op.add_column(
        "verifications",
        sa.Column("country", sa.String(), nullable=False, server_default="US"),
    )


def downgrade():
    # Remove country column from verifications table
    op.drop_column("verifications", "country")
