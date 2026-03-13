"""add_assigned_filters

Revision ID: 6773ecc277a0
Revises: 004_add_verification_outcome
Create Date: 2026-03-13 20:54:48.460789

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6773ecc277a0'
down_revision = '004_add_verification_outcome'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('verifications', sa.Column('assigned_area_code', sa.String(length=10), nullable=True))
    op.add_column('verifications', sa.Column('assigned_carrier', sa.String(length=50), nullable=True))
    op.add_column('verifications', sa.Column('fallback_applied', sa.Boolean(), server_default='False', nullable=True))
    op.add_column('verifications', sa.Column('same_state_fallback', sa.Boolean(), server_default='True', nullable=True))

def downgrade() -> None:
    op.drop_column('verifications', 'same_state_fallback')
    op.drop_column('verifications', 'fallback_applied')
    op.drop_column('verifications', 'assigned_carrier')
    op.drop_column('verifications', 'assigned_area_code')