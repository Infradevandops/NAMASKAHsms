"""Add pricing enforcement schema.

Revision ID: 001_pricing_enforcement
Revises:
Create Date: 2025-12-27
"""

import sqlalchemy as sa
from alembic import op


revision = "001_pricing_enforcement"
down_revision = "pricing_templates_v1"
branch_labels = None
depends_on = None


def _column_exists(table, column):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns(table)]
    return column in columns
 
 
def _table_exists(table):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    return table in tables


def upgrade():
    if not _table_exists("users"):
        return
    if not _column_exists("users", "bonus_sms_balance"):
        op.add_column("users", sa.Column("bonus_sms_balance", sa.Float(), nullable=False, server_default="0.0"))
    if not _column_exists("users", "monthly_quota_used"):
        op.add_column("users", sa.Column("monthly_quota_used", sa.Float(), nullable=False, server_default="0.0"))
    if not _column_exists("users", "monthly_quota_reset_date"):
        op.add_column("users", sa.Column("monthly_quota_reset_date", sa.Date(), nullable=True))

    if not _table_exists("monthly_quota_usage"):
        op.create_table(
            "monthly_quota_usage",
            sa.Column("id", sa.String(50), nullable=False),
            sa.Column("user_id", sa.String(50), nullable=False),
            sa.Column("month", sa.String(7), nullable=False),
            sa.Column("quota_used", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("overage_used", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.UniqueConstraint("user_id", "month", name="uq_user_month"),
        )
        op.create_index("ix_monthly_quota_usage_user_id", "monthly_quota_usage", ["user_id"])
        op.create_index("ix_monthly_quota_usage_month", "monthly_quota_usage", ["month"])


def downgrade():

    op.drop_index("ix_monthly_quota_usage_month", table_name="monthly_quota_usage")
    op.drop_index("ix_monthly_quota_usage_user_id", table_name="monthly_quota_usage")
    op.drop_table("monthly_quota_usage")
    op.drop_column("users", "monthly_quota_reset_date")
    op.drop_column("users", "monthly_quota_used")
    op.drop_column("users", "bonus_sms_balance")
