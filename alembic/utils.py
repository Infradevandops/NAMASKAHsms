"""Shared idempotency helpers for Alembic migrations."""
import sqlalchemy as sa
from alembic import op


def column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    return bind.execute(
        sa.text("SELECT 1 FROM information_schema.columns WHERE table_name=:t AND column_name=:c")
        .bindparams(t=table, c=column)
    ).fetchone() is not None


def table_exists(table: str) -> bool:
    bind = op.get_bind()
    return bind.execute(
        sa.text("SELECT 1 FROM information_schema.tables WHERE table_name=:t")
        .bindparams(t=table)
    ).fetchone() is not None


def index_exists(index: str) -> bool:
    bind = op.get_bind()
    return bind.execute(
        sa.text("SELECT 1 FROM pg_indexes WHERE indexname=:i")
        .bindparams(i=index)
    ).fetchone() is not None
