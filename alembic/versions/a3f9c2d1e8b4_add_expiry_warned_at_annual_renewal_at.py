"""add expiry_warned_at and annual_renewal_at columns (already applied)

Revision ID: a3f9c2d1e8b4
Revises: 39eb936fe739
Create Date: 2026-11-25

Columns were applied directly via psql. This file exists so Alembic
can locate the revision that is stamped in alembic_version.
"""

from alembic import op

revision = "a3f9c2d1e8b4"
down_revision = "39eb936fe739"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE number_rentals ADD COLUMN IF NOT EXISTS expiry_warned_at TIMESTAMPTZ"
    )
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS annual_renewal_at TIMESTAMPTZ"
    )


def downgrade() -> None:
    pass
