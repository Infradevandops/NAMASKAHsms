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
def upgrade():
    """Add idempotency and state tracking to payment tables."""
    # Add to transactions table
    op.add_column("transactions", sa.Column("reference", sa.String(), nullable=True))
    op.add_column("transactions", sa.Column("idempotency_key", sa.String(), nullable=True))
    op.add_column("transactions", sa.Column("payment_log_id", sa.String(), nullable=True))
    op.create_index("ix_transactions_reference", "transactions", ["reference"], unique=True)
    op.create_index("ix_transactions_idempotency_key", "transactions", ["idempotency_key"], unique=True)
    op.create_index("ix_transactions_payment_log_id", "transactions", ["payment_log_id"], unique=False)
    # Add to payment_logs table
    op.add_column("payment_logs", sa.Column("idempotency_key", sa.String(), nullable=True))
    op.add_column("payment_logs", sa.Column("processing_started_at", sa.DateTime(), nullable=True))
    op.add_column("payment_logs", sa.Column("processing_completed_at", sa.DateTime(), nullable=True))
    op.add_column("payment_logs", sa.Column("state", sa.String(20), nullable=True, server_default="pending"))
    op.add_column("payment_logs", sa.Column("state_transitions", sa.JSON(), nullable=True))
    op.add_column("payment_logs", sa.Column("lock_version", sa.Integer(), nullable=False, server_default="0"))
    op.create_index("ix_payment_logs_idempotency_key", "payment_logs", ["idempotency_key"], unique=True)
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