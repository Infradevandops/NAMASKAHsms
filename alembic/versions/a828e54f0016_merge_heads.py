"""merge heads

Revision ID: a828e54f0016
Revises: 06e5fe3aacd9, add_sms_forwarding_model
Create Date: 2025-11-21 02:00:15.522844

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a828e54f0016'
down_revision = ('06e5fe3aacd9', 'add_sms_forwarding_model')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass