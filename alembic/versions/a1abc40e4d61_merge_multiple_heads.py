"""merge multiple heads

Revision ID: a1abc40e4d61
Revises: c5d8e9f1a2b3, d6e7f8g9h0i1
Create Date: 2026-04-25 01:31:40.722035

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1abc40e4d61'
down_revision = ('c5d8e9f1a2b3', 'd6e7f8g9h0i1')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass