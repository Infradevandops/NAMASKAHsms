"""merge_migration_heads

Revision ID: 061d9956377d
Revises: 000_initial_schema, fix_monetary_float_columns
Create Date: 2026-04-16 19:21:23.255587

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '061d9956377d'
down_revision = ('000_initial_schema', 'fix_monetary_float_columns')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass