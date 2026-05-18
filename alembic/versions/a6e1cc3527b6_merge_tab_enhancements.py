"""merge_tab_enhancements

Revision ID: a6e1cc3527b6
Revises: add_dispute_enhancements, f9a8b7c6d5e4
Create Date: 2026-05-18 12:57:47.203990

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a6e1cc3527b6"
down_revision = ("add_dispute_enhancements", "f9a8b7c6d5e4")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
