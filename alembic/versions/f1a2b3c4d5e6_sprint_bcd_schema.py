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
    conn = op.get_bind()

    # M-001: verifications columns
    for col in ["reusable_until", "reused_from_id", "ends_at"]:
        conn.execute(sa.text(f"ALTER TABLE verifications ADD COLUMN IF NOT EXISTS {col} {'VARCHAR' if col == 'reused_from_id' else 'TIMESTAMP'}"))

    # M-002: subscriptions columns
    conn.execute(sa.text("ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS billing_period VARCHAR(10) NOT NULL DEFAULT 'monthly'"))
    conn.execute(sa.text("ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS annual_renewal_at TIMESTAMP"))

    # M-003: subscription_addons
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS subscription_addons (
            id VARCHAR PRIMARY KEY,
            user_id VARCHAR NOT NULL,
            addon_type VARCHAR(50) NOT NULL,
            price_usd NUMERIC(10,2) NOT NULL,
            active BOOLEAN NOT NULL DEFAULT true,
            started_at TIMESTAMP NOT NULL,
            expires_at TIMESTAMP,
            paystack_subscription_code VARCHAR(100),
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            CONSTRAINT uq_user_addon_type UNIQUE (user_id, addon_type)
        )
    """))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_subscription_addons_user_id ON subscription_addons (user_id)"))

    # M-004: stock_watches
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS stock_watches (
            id VARCHAR PRIMARY KEY,
            user_id VARCHAR NOT NULL,
            service_name VARCHAR(100) NOT NULL,
            capability VARCHAR(20) NOT NULL DEFAULT 'sms',
            notified_at TIMESTAMP,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            CONSTRAINT uq_stock_watch UNIQUE (user_id, service_name, capability)
        )
    """))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_stock_watches_user_id ON stock_watches (user_id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_stock_watches_service_name ON stock_watches (service_name)"))

    # M-005: rental_back_orders
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS rental_back_orders (
            id VARCHAR PRIMARY KEY,
            user_id VARCHAR NOT NULL,
            tv_back_order_id VARCHAR(100) NOT NULL UNIQUE,
            service_name VARCHAR(100) NOT NULL,
            capability VARCHAR(20) NOT NULL DEFAULT 'sms',
            credits_held NUMERIC(10,4) NOT NULL,
            fulfilled_at TIMESTAMP,
            notified_at TIMESTAMP,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    """))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_rental_back_orders_user_id ON rental_back_orders (user_id)"))

    # M-006: number_rentals
    conn.execute(sa.text("ALTER TABLE number_rentals ADD COLUMN IF NOT EXISTS expiry_warned_at TIMESTAMP"))


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
