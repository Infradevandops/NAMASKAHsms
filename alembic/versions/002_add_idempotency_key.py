"""Add idempotency_key to verifications table

Revision ID: 002_add_idempotency_key
Revises: 001_pricing_enforcement
Create Date: 2026-01-22

"""

from alembic import op
import sqlalchemy as sa

revision = "002_add_idempotency_key"
down_revision = "pricing_templates_v1"
branch_labels = None
depends_on = None


def upgrade():
    """Add idempotency_key column to verifications table."""
    op.add_column(
        "verifications",
        sa.Column("idempotency_key", sa.String(), nullable=True)
    )
    op.create_index(
        "ix_verifications_idempotency_key", 
        "verifications", 
        ["idempotency_key"], 
        unique=False
    )


def downgrade():
    """Remove idempotency_key column from verifications table."""
    op.drop_index("ix_verifications_idempotency_key", table_name="verifications")
    op.drop_column("verifications", "idempotency_key")