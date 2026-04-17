"""Add payment idempotency and state machine

Revision ID: 003_payment_idempotency
Revises: 002_add_idempotency_key
Create Date: 2026-01-26

"""

import sqlalchemy as sa
from alembic import op

revision = "003_payment_idempotency"
down_revision = "002_add_idempotency_key"
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
    if not _table_exists("transactions"):
        return
    for col in ["reference", "idempotency_key", "payment_log_id"]:
        if not _column_exists("transactions", col):
            op.add_column("transactions", sa.Column(col, sa.String(), nullable=True))
    if not _index_exists("transactions", "ix_transactions_reference"):
        op.create_index("ix_transactions_reference", "transactions", ["reference"], unique=True)
    if not _index_exists("transactions", "ix_transactions_idempotency_key"):
        op.create_index("ix_transactions_idempotency_key", "transactions", ["idempotency_key"], unique=True)
    if not _index_exists("transactions", "ix_transactions_payment_log_id"):
        op.create_index("ix_transactions_payment_log_id", "transactions", ["payment_log_id"], unique=False)
 
    pl_cols = [
        ("idempotency_key", sa.String(), True),
        ("processing_started_at", sa.DateTime(), True),
        ("processing_completed_at", sa.DateTime(), True),
        ("state", sa.String(20), True),
        ("state_transitions", sa.JSON(), True),
        ("lock_version", sa.Integer(), False),
    ]
    defaults = {"state": "pending", "lock_version": "0"}
    for col_name, col_type, nullable in pl_cols:
        if not _column_exists("payment_logs", col_name):
            kw = {"nullable": nullable}
            if col_name in defaults:
                kw["server_default"] = defaults[col_name]
            op.add_column("payment_logs", sa.Column(col_name, col_type, **kw))
    if not _index_exists("payment_logs", "ix_payment_logs_idempotency_key"):
        op.create_index("ix_payment_logs_idempotency_key", "payment_logs", ["idempotency_key"], unique=True)
    if not _index_exists("payment_logs", "ix_payment_logs_state"):
        op.create_index("ix_payment_logs_state", "payment_logs", ["state"], unique=False)
def downgrade():
    """Remove idempotency and state tracking."""
    # Remove from payment_logs
    op.drop_index("ix_payment_logs_state", table_name="payment_logs")
    op.drop_index("ix_payment_logs_idempotency_key", table_name="payment_logs")
    op.drop_column("payment_logs", "lock_version")
    op.drop_column("payment_logs", "state_transitions")
    op.drop_column("payment_logs", "state")
    op.drop_column("payment_logs", "processing_completed_at")
    op.drop_column("payment_logs", "processing_started_at")
    op.drop_column("payment_logs", "idempotency_key")
    # Remove from transactions
    op.drop_index("ix_transactions_payment_log_id", table_name="transactions")
    op.drop_index("ix_transactions_idempotency_key", table_name="transactions")
    op.drop_index("ix_transactions_reference", table_name="transactions")
    op.drop_column("transactions", "payment_log_id")
    op.drop_column("transactions", "idempotency_key")
    op.drop_column("transactions", "reference")