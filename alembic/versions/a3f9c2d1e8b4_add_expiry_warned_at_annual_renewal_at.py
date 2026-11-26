"""add expiry_warned_at and annual_renewal_at columns

Revision ID: a3f9c2d1e8b4
Revises: 39eb936fe739
Create Date: 2026-11-25

"""

from alembic import op
import sqlalchemy as sa

revision = "a3f9c2d1e8b4"
down_revision = "39eb936fe739"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE number_rentals ADD COLUMN IF NOT EXISTS expiry_warned_at TIMESTAMP WITH TIME ZONE"
    )
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS annual_renewal_at TIMESTAMP WITH TIME ZONE"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE number_rentals DROP COLUMN IF EXISTS expiry_warned_at")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS annual_renewal_at")
