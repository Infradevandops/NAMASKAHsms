"""add_retry_tracking_v4_4_1

Revision ID: 2bf41b9c69d1
Revises: 6773ecc277a0
Create Date: 2026-03-17 23:44:26.652055

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2bf41b9c69d1'
down_revision = '6773ecc277a0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add retry tracking fields for v4.4.1
    op.add_column('verifications', sa.Column('retry_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('verifications', sa.Column('area_code_matched', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('verifications', sa.Column('carrier_matched', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('verifications', sa.Column('real_carrier', sa.String(), nullable=True))
    op.add_column('verifications', sa.Column('carrier_surcharge', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('verifications', sa.Column('area_code_surcharge', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('verifications', sa.Column('voip_rejected', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    # Remove retry tracking fields
    op.drop_column('verifications', 'voip_rejected')
    op.drop_column('verifications', 'area_code_surcharge')
    op.drop_column('verifications', 'carrier_surcharge')
    op.drop_column('verifications', 'real_carrier')
    op.drop_column('verifications', 'carrier_matched')
    op.drop_column('verifications', 'area_code_matched')
    op.drop_column('verifications', 'retry_attempts')