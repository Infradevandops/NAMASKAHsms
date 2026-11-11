"""Sprint B/C/D schema additions.

Covers:
  M-001 (B-009): verifications.reusable_until, verifications.reused_from_id, verifications.ends_at
  M-002 (C-002): subscriptions.billing_period, subscriptions.annual_renewal_at
  M-003 (C-008): subscription_addons table
  M-004 (D-001): stock_watches table
  M-005 (D-008): rental_back_orders table
  M-006 (D-016): number_rentals.expiry_warned_at

Revision ID: f1a2b3c4d5e6
Revises: merge_all_heads
Create Date: 2026-11-20
"""

from alembic import op
import sqlalchemy as sa

revision = "f1a2b3c4d5e6"
down_revision = "merge_all_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # M-001: verifications — reuse + ends_at columns
    with op.batch_alter_table("verifications") as batch_op:
        batch_op.add_column(sa.Column("reusable_until", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("reused_from_id", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("ends_at", sa.DateTime(), nullable=True))

    # M-002: subscriptions — annual billing
    with op.batch_alter_table("subscriptions", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("billing_period", sa.String(10), nullable=False, server_default="monthly")
        )
        batch_op.add_column(sa.Column("annual_renewal_at", sa.DateTime(), nullable=True))

    # M-003: subscription_addons table
    op.create_table(
        "subscription_addons",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("addon_type", sa.String(50), nullable=False),
        sa.Column("price_usd", sa.Numeric(10, 2), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("paystack_subscription_code", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "addon_type", name="uq_user_addon_type"),
    )
    op.create_index("ix_subscription_addons_user_id", "subscription_addons", ["user_id"])

    # M-004: stock_watches table
    op.create_table(
        "stock_watches",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("service_name", sa.String(100), nullable=False),
        sa.Column("capability", sa.String(20), nullable=False, server_default="sms"),
        sa.Column("notified_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "service_name", "capability", name="uq_stock_watch"),
    )
    op.create_index("ix_stock_watches_user_id", "stock_watches", ["user_id"])
    op.create_index("ix_stock_watches_service_name", "stock_watches", ["service_name"])

    # M-005: rental_back_orders table
    op.create_table(
        "rental_back_orders",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("tv_back_order_id", sa.String(100), nullable=False),
        sa.Column("service_name", sa.String(100), nullable=False),
        sa.Column("capability", sa.String(20), nullable=False, server_default="sms"),
        sa.Column("credits_held", sa.Numeric(10, 4), nullable=False),
        sa.Column("fulfilled_at", sa.DateTime(), nullable=True),
        sa.Column("notified_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tv_back_order_id"),
    )
    op.create_index("ix_rental_back_orders_user_id", "rental_back_orders", ["user_id"])

    # M-006: number_rentals — expiry warning column
    with op.batch_alter_table("number_rentals") as batch_op:
        batch_op.add_column(sa.Column("expiry_warned_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("number_rentals") as batch_op:
        batch_op.drop_column("expiry_warned_at")

    op.drop_table("rental_back_orders")
    op.drop_table("stock_watches")
    op.drop_table("subscription_addons")

    with op.batch_alter_table("subscriptions", schema=None) as batch_op:
        batch_op.drop_column("annual_renewal_at")
        batch_op.drop_column("billing_period")

    with op.batch_alter_table("verifications") as batch_op:
        batch_op.drop_column("ends_at")
        batch_op.drop_column("reused_from_id")
        batch_op.drop_column("reusable_until")
