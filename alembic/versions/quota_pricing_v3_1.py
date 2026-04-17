"""Migrate to Quota-Based Pricing Model

Revision ID: quota_pricing_v3_1
Created: 2025-12-25
"""

import sqlalchemy as sa
from alembic import op


# revision identifiers
revision = "quota_pricing_v3_1"
down_revision = "add_user_preferences"
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade to quota-based pricing"""

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # Skip entirely if base tables don't exist yet (fresh DB - lifespan will create them)
    if "users" not in existing_tables:
        return

    # 1. Create tiers table if missing, otherwise add new columns
    if "tiers" not in existing_tables:
        op.create_table(
            "tiers",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("tier_name", sa.String(50), nullable=False),
            sa.Column("monthly_price", sa.DECIMAL(10, 2), nullable=True),
            sa.Column("included_quota", sa.DECIMAL(10, 2), server_default="0.00"),
            sa.Column("overage_rate", sa.DECIMAL(10, 2), nullable=True),
            sa.Column("single_sms_rate", sa.DECIMAL(10, 2), nullable=True),
            sa.Column("api_keys_limit", sa.Integer(), nullable=True),
            sa.Column("features", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("tier_name"),
        )
    else:
        existing_cols = [c["name"] for c in inspector.get_columns("tiers")]
        if "included_quota" not in existing_cols:
            op.add_column("tiers", sa.Column("included_quota", sa.DECIMAL(10, 2), server_default="0.00"))
        if "overage_rate" not in existing_cols:
            op.add_column("tiers", sa.Column("overage_rate", sa.DECIMAL(10, 2), nullable=True))
        if "single_sms_rate" not in existing_cols:
            op.add_column("tiers", sa.Column("single_sms_rate", sa.DECIMAL(10, 2), nullable=True))

    # 2. Add quota tracking columns to users table
    if "users" in existing_tables:
        user_cols = [c["name"] for c in inspector.get_columns("users")]
        if "quota_balance" not in user_cols:
            op.add_column("users", sa.Column("quota_balance", sa.DECIMAL(10, 2), server_default="0.00"))
        if "quota_reset_date" not in user_cols:
            op.add_column("users", sa.Column("quota_reset_date", sa.TIMESTAMP, nullable=True))
        if "total_overage_charges" not in user_cols:
            op.add_column("users", sa.Column("total_overage_charges", sa.DECIMAL(10, 2), server_default="0.00"))

    # 3. Create quota_transactions table
    if "quota_transactions" not in existing_tables:
        op.create_table(
            "quota_transactions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("transaction_type", sa.String(50), nullable=False),
            sa.Column("amount", sa.DECIMAL(10, 2), nullable=False),
            sa.Column("balance_before", sa.DECIMAL(10, 2), nullable=False),
            sa.Column("balance_after", sa.DECIMAL(10, 2), nullable=False),
            sa.Column("verification_id", sa.String(), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["verification_id"], ["verifications.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("idx_quota_transactions_user", "quota_transactions", ["user_id"])
        op.create_index("idx_quota_transactions_created", "quota_transactions", ["created_at"])

    # 4. Seed / update tier data
    connection = op.get_bind()
    is_sqlite = connection.dialect.name == "sqlite"
 
    # Helper to handle JSON casting
    json_cast = "" if is_sqlite else "::jsonb"
 
    connection.execute(sa.text("""
        UPDATE tiers SET monthly_price = 0.00, included_quota = 5.00,
            overage_rate = NULL, single_sms_rate = NULL
        WHERE tier_name = 'trial'
    """))
 
    connection.execute(sa.text("""
        UPDATE tiers SET monthly_price = 0.00, included_quota = 0.00,
            overage_rate = 2.50, single_sms_rate = 2.75
        WHERE tier_name IN ('payg', 'pay_as_you_go')
    """))
 
    connection.execute(sa.text("""
        UPDATE tiers SET monthly_price = 8.99, included_quota = 10.00,
            overage_rate = 2.30, single_sms_rate = NULL
        WHERE tier_name = 'starter'
    """))
 
    # Insert or Update tiers with cross-dialect JSON support
    for tier, price, quota, rate, api_limit, features in [
        ('turbo', 25.00, 30.00, 2.20, 10, '["area_code_selection", "isp_filtering", "api_access"]'),
        ('pro', 49.00, 65.00, 2.10, None, '["area_code_selection", "isp_filtering", "api_access", "priority_support"]'),
        ('custom', None, None, 2.00, None, '["all"]')
    ]:
        if is_sqlite:
            connection.execute(sa.text(f"""
                INSERT OR REPLACE INTO tiers (tier_name, monthly_price, included_quota, overage_rate, api_keys_limit, features, created_at)
                VALUES (:name, :price, :quota, :rate, :limit, :features, CURRENT_TIMESTAMP)
            """), {"name": tier, "price": price, "quota": quota, "rate": rate, "limit": api_limit, "features": features})
        else:
            connection.execute(sa.text(f"""
                INSERT INTO tiers (tier_name, monthly_price, included_quota, overage_rate, api_keys_limit, features, created_at)
                VALUES (:name, :price, :quota, :rate, :limit, :features::jsonb, CURRENT_TIMESTAMP)
                ON CONFLICT (tier_name) DO UPDATE SET
                    monthly_price = :price, included_quota = :quota, overage_rate = :rate, api_keys_limit = :limit
            """), {"name": tier, "price": price, "quota": quota, "rate": rate, "limit": api_limit, "features": features})
 
    # 5+6. Only seed user quotas if subscription_tier column already exists
    user_cols = [c["name"] for c in inspector.get_columns("users")]
    if "subscription_tier" in user_cols:
        if is_sqlite:
            # SQLite update-from is different
            connection.execute(sa.text("""
                UPDATE users SET
                    quota_balance = (SELECT included_quota FROM tiers WHERE tiers.tier_name = users.subscription_tier),
                    quota_reset_date = date('now', 'start of month', '+1 month')
                WHERE EXISTS (SELECT 1 FROM tiers WHERE tiers.tier_name = users.subscription_tier)
            """))
        else:
            connection.execute(sa.text("""
                UPDATE users u
                SET quota_balance = t.included_quota,
                    quota_reset_date = DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
                FROM tiers t
                WHERE u.subscription_tier = t.tier_name
            """))
            
        connection.execute(sa.text("""
            INSERT INTO quota_transactions (user_id, transaction_type, amount, balance_before, balance_after, description)
            SELECT u.id, 'quota_reset', t.included_quota, 0.00, t.included_quota,
                   'Initial quota allocation (migration)'
            FROM users u
            JOIN tiers t ON u.subscription_tier = t.tier_name
            WHERE t.included_quota > 0
        """))

    print("✅ Migration to quota-based pricing completed successfully")


def downgrade():
    """Downgrade from quota-based pricing"""

    op.drop_column("users", "total_overage_charges")
    op.drop_column("users", "quota_reset_date")
    op.drop_column("users", "quota_balance")

    op.drop_index("idx_quota_transactions_created", "quota_transactions")
    op.drop_index("idx_quota_transactions_user", "quota_transactions")
    op.drop_table("quota_transactions")

    op.drop_column("tiers", "single_sms_rate")
    op.drop_column("tiers", "overage_rate")
    op.drop_column("tiers", "included_quota")

    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE tiers SET monthly_price = 29.00 WHERE tier_name = 'starter';
        UPDATE tiers SET monthly_price = 99.00 WHERE tier_name = 'professional';
        DELETE FROM tiers WHERE tier_name IN ('turbo', 'pro', 'custom');
    """))

    print("⚠️ Downgraded from quota-based pricing")
