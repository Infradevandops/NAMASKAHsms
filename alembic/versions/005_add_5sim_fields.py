"""Add 5SIM fields to verifications

Revision ID: 005
Revises: 004
Create Date: 2025-11-04 01:05:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 5SIM specific fields to verifications table
    op.add_column("verifications", sa.Column("provider", sa.String(20), default="5sim"))
    op.add_column("verifications", sa.Column("fivesim_activation_id", sa.String(50)))
    op.add_column("verifications", sa.Column("fivesim_phone_number", sa.String(20)))
    op.add_column("verifications", sa.Column("fivesim_cost", sa.Numeric(10, 4)))


def downgrade() -> None:
    op.drop_column("verifications", "fivesim_cost")
    op.drop_column("verifications", "fivesim_phone_number")
    op.drop_column("verifications", "fivesim_activation_id")
    op.drop_column("verifications", "provider")
