"""Add idempotency_key to verifications table

Revision ID: 002_add_idempotency_key
Revises: 001_pricing_enforcement
Create Date: 2026-01-22
"""

import sqlalchemy as sa
from alembic import op


revision = "002_add_idempotency_key"
down_revision = "001_pricing_enforcement"
branch_labels = None
depends_on = None


def _column_exists(table, column):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns(table)]
    return column in columns
 
 
def _index_exists(table, index):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = [i["name"] for i in inspector.get_indexes(table)]
    return index in indexes
 
 
def _table_exists(table):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    return table in tables


def upgrade():
    if not _table_exists("verifications"):
        return
    if not _column_exists("verifications", "idempotency_key"):
        op.add_column("verifications", sa.Column("idempotency_key", sa.String(), nullable=True))
    if not _index_exists("verifications", "ix_verifications_idempotency_key"):
        op.create_index("ix_verifications_idempotency_key", "verifications", ["idempotency_key"], unique=False)


def downgrade():

    """Remove idempotency_key column from verifications table."""
    op.drop_index("ix_verifications_idempotency_key", table_name="verifications")
    op.drop_column("verifications", "idempotency_key")
