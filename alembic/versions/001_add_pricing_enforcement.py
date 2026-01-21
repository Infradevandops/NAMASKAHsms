"""Add pricing enforcement schema.

Revision ID: 001_pricing_enforcement
Revises: 
Create Date: 2025-12-27

"""

from alembic import op
import sqlalchemy as sa


revision = "001_pricing_enforcement"
down_revision = "pricing_templates_v1"
branch_labels = None
depends_on = None


def upgrade():
    # Add columns to users table
    op.add_column(
        "users",
        sa.Column(
            "bonus_sms_balance", sa.Float(), nullable=False, server_default="0.0"
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "monthly_quota_used", sa.Float(), nullable=False, server_default="0.0"
        ),
    )
    op.add_column(
        "users", sa.Column("monthly_quota_reset_date", sa.Date(), nullable=True)
    )

    # Create monthly_quota_usage table
    op.create_table(
        "monthly_quota_usage",
        sa.Column("id", sa.String(50), nullable=False),
        sa.Column("user_id", sa.String(50), nullable=False),
        sa.Column("month", sa.String(7), nullable=False),  # "2025-01"
        sa.Column("quota_used", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("overage_used", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.UniqueConstraint("user_id", "month", name="uq_user_month"),
    )
    op.create_index(
        "ix_monthly_quota_usage_user_id", "monthly_quota_usage", ["user_id"]
    )
    op.create_index("ix_monthly_quota_usage_month", "monthly_quota_usage", ["month"])


def downgrade():
    op.drop_index("ix_monthly_quota_usage_month", table_name="monthly_quota_usage")
    op.drop_index("ix_monthly_quota_usage_user_id", table_name="monthly_quota_usage")
    op.drop_table("monthly_quota_usage")
    op.drop_column("users", "monthly_quota_reset_date")
    op.drop_column("users", "monthly_quota_used")
    op.drop_column("users", "bonus_sms_balance")
