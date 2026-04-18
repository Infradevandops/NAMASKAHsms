"""add credit hold and reconciliation fields to users

Revision ID: c5d8e9f1a2b3
Revises: b1279f965154
Create Date: 2026-04-18 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c5d8e9f1a2b3'
down_revision = '840995b58a0b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add credit hold and reconciliation tracking fields to users table."""
    # Use inspector for safe column addition
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    try:
        columns = [c["name"] for c in inspector.get_columns("users")]
    except Exception:
        columns = []
    
    # Add credit hold fields
    if "credit_hold_amount" not in columns:
        op.add_column(
            "users",
            sa.Column(
                "credit_hold_amount",
                sa.Numeric(precision=10, scale=4),
                nullable=False,
                server_default="0.0"
            )
        )
    
    if "credit_hold_reason" not in columns:
        op.add_column(
            "users",
            sa.Column("credit_hold_reason", sa.String(), nullable=True)
        )
    
    if "credit_hold_until" not in columns:
        op.add_column(
            "users",
            sa.Column("credit_hold_until", sa.DateTime(), nullable=True)
        )
    
    # Add reconciliation tracking field
    if "last_reconciliation_at" not in columns:
        op.add_column(
            "users",
            sa.Column("last_reconciliation_at", sa.DateTime(), nullable=True)
        )
    
    # Create indices for performance
    try:
        op.create_index(
            "ix_users_credit_hold_until",
            "users",
            ["credit_hold_until"],
            unique=False
        )
    except Exception:
        pass  # Index might already exist
    
    try:
        op.create_index(
            "ix_users_last_reconciliation_at",
            "users",
            ["last_reconciliation_at"],
            unique=False
        )
    except Exception:
        pass  # Index might already exist


def downgrade() -> None:
    """Remove credit hold and reconciliation fields from users table."""
    # Drop indices first
    try:
        op.drop_index("ix_users_last_reconciliation_at", table_name="users")
    except Exception:
        pass
    
    try:
        op.drop_index("ix_users_credit_hold_until", table_name="users")
    except Exception:
        pass
    
    # Drop columns
    op.drop_column("users", "last_reconciliation_at")
    op.drop_column("users", "credit_hold_until")
    op.drop_column("users", "credit_hold_reason")
    op.drop_column("users", "credit_hold_amount")
