"""add outcome columns to verifications

Revision ID: 004_add_verification_outcome
Revises: add_preferred_area_codes
Create Date: 2026-03-08
"""
from alembic import op
import sqlalchemy as sa

revision = "004_add_verification_outcome"
down_revision = "add_preferred_area_codes"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if "verifications" in inspector.get_table_names():
        existing_columns = [col["name"] for col in inspector.get_columns("verifications")]
        
        if "outcome" not in existing_columns:
            op.add_column("verifications", sa.Column("outcome", sa.String(), nullable=True))
        if "cancel_reason" not in existing_columns:
            op.add_column("verifications", sa.Column("cancel_reason", sa.String(), nullable=True))
        if "error_message" not in existing_columns:
            op.add_column("verifications", sa.Column("error_message", sa.String(), nullable=True))


def downgrade():
    op.drop_column("verifications", "error_message")
    op.drop_column("verifications", "cancel_reason")
    op.drop_column("verifications", "outcome")
