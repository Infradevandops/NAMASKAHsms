"""add_bulk_id_to_verifications

Revision ID: 06e5fe3aacd9
Revises: 001_consolidated
Create Date: 2025-11-17 23:54:11.954309

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '06e5fe3aacd9'
down_revision = '001_consolidated'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add bulk_id column to verifications table
    op.add_column('verifications', sa.Column('bulk_id', sa.String(), nullable=True))
    op.create_index('ix_verifications_bulk_id', 'verifications', ['bulk_id'])


def downgrade() -> None:
    # Remove bulk_id column from verifications table
    op.drop_index('ix_verifications_bulk_id', 'verifications')
    op.drop_column('verifications', 'bulk_id')