"""merge migration heads

Revision ID: cb2a98627849
Revises: 001_add_subscription_tiers, f6a9a9aafab3
Create Date: 2025-12-11 01:50:30.566417

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cb2a98627849'
down_revision = ('001_add_subscription_tiers', 'f6a9a9aafab3')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass