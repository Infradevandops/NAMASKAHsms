"""Add affiliate system tables

Revision ID: 012_add_affiliate_system
Revises: 011_add_enterprise_tables
Create Date: 2024-01-15 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers
revision = "012_add_affiliate_system"
down_revision = "011_add_enterprise_tables"
branch_labels = None
depends_on = None


def upgrade():
    # Create affiliate_programs table
    op.create_table(
        "affiliate_programs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "program_type", sa.String(length=50), nullable=False
        ),  # 'referral' or 'enterprise'
        sa.Column("commission_rate", sa.Float(), nullable=False),
        sa.Column("tier_requirements", sa.JSON(), nullable=True),
        sa.Column("features", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create affiliate_applications table
    op.create_table(
        "affiliate_applications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("program_type", sa.String(length=50), nullable=False),
        sa.Column("program_options", sa.JSON(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), default="pending"),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create affiliate_commissions table
    op.create_table(
        "affiliate_commissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("affiliate_id", sa.Integer(), nullable=False),
        sa.Column("transaction_id", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("commission_rate", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=50), default="pending"),
        sa.Column("payout_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["affiliate_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Add affiliate fields to users table
    op.add_column(
        "users", sa.Column("affiliate_id", sa.String(length=50), nullable=True)
    )
    op.add_column(
        "users", sa.Column("partner_type", sa.String(length=50), nullable=True)
    )
    op.add_column(
        "users", sa.Column("commission_tier", sa.String(length=50), nullable=True)
    )
    op.add_column("users", sa.Column("is_affiliate", sa.Boolean(), default=False))


def downgrade():
    op.drop_column("users", "is_affiliate")
    op.drop_column("users", "commission_tier")
    op.drop_column("users", "partner_type")
    op.drop_column("users", "affiliate_id")
    op.drop_table("affiliate_commissions")
    op.drop_table("affiliate_applications")
    op.drop_table("affiliate_programs")
