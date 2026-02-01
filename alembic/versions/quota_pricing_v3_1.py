"""
import sqlalchemy as sa
from alembic import op

Migrate to Quota-Based Pricing Model

Revision ID: quota_pricing_v3_1
Created: 2025-12-25
"""


# revision identifiers
revision = "quota_pricing_v3_1"
down_revision = "add_user_preferences"
branch_labels = None
depends_on = None


def upgrade():

    """Upgrade to quota-based pricing"""

    # 1. Add new columns to tiers table
    op.add_column(
        "tiers", sa.Column("included_quota", sa.DECIMAL(10, 2), server_default="0.00")
    )
    op.add_column("tiers", sa.Column("overage_rate", sa.DECIMAL(10, 2), nullable=True))
    op.add_column(
        "tiers", sa.Column("single_sms_rate", sa.DECIMAL(10, 2), nullable=True)
    )

    # 2. Add quota tracking to users table
    op.add_column(
        "users", sa.Column("quota_balance", sa.DECIMAL(10, 2), server_default="0.00")
    )
    op.add_column("users", sa.Column("quota_reset_date", sa.TIMESTAMP, nullable=True))
    op.add_column(
        "users",
        sa.Column("total_overage_charges", sa.DECIMAL(10, 2), server_default="0.00"),
    )

    # 3. Create quota_transactions table
    op.create_table(
        "quota_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("transaction_type", sa.String(50), nullable=False),
        sa.Column("amount", sa.DECIMAL(10, 2), nullable=False),
        sa.Column("balance_before", sa.DECIMAL(10, 2), nullable=False),
        sa.Column("balance_after", sa.DECIMAL(10, 2), nullable=False),
        sa.Column("verification_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["verification_id"], ["verifications.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("idx_quota_transactions_user", "quota_transactions", ["user_id"])
    op.create_index(
        "idx_quota_transactions_created", "quota_transactions", ["created_at"]
    )

    # 4. Update existing tier data
    connection = op.get_bind()

    # Update Trial tier
    connection.execute(
        sa.text(
            """
        UPDATE tiers
        SET
            monthly_price = 0.00,
            included_quota = 5.00,
            overage_rate = NULL,
            single_sms_rate = NULL
        WHERE tier_name = 'trial'
    """
        )
    )

    # Update Pay-As-You-Go tier
    connection.execute(
        sa.text(
            """
        UPDATE tiers
        SET
            monthly_price = 0.00,
            included_quota = 0.00,
            overage_rate = 2.50,
            single_sms_rate = 2.75
        WHERE tier_name = 'payg' OR tier_name = 'pay_as_you_go'
    """
        )
    )

    # Update Starter tier
    connection.execute(
        sa.text(
            """
        UPDATE tiers
        SET
            monthly_price = 8.99,
            included_quota = 10.00,
            overage_rate = 2.30,
            single_sms_rate = NULL
        WHERE tier_name = 'starter'
    """
        )
    )

    # Insert new Turbo tier (if not exists)
    connection.execute(
        sa.text(
            """
        INSERT INTO tiers (tier_name, monthly_price, included_quota, overage_rate, api_keys_limit, features, created_at)
        VALUES ('turbo', 25.00, 30.00, 2.20, 10,
                '["area_code_selection", "isp_filtering", "api_access"]'::jsonb,
                CURRENT_TIMESTAMP)
        ON CONFLICT (tier_name) DO UPDATE SET
            monthly_price = 25.00,
            included_quota = 30.00,
            overage_rate = 2.20,
            api_keys_limit = 10
    """
        )
    )

    # Insert new Pro tier (if not exists)
    connection.execute(
        sa.text(
            """
        INSERT INTO tiers (tier_name, monthly_price, included_quota, overage_rate, api_keys_limit, features, created_at)
        VALUES ('pro', 49.00, 65.00, 2.10, NULL,
                '["area_code_selection", "isp_filtering", "api_access", "priority_support"]'::jsonb,
                CURRENT_TIMESTAMP)
        ON CONFLICT (tier_name) DO UPDATE SET
            monthly_price = 49.00,
            included_quota = 65.00,
            overage_rate = 2.10,
            api_keys_limit = NULL
    """
        )
    )

    # Insert Custom tier (if not exists)
    connection.execute(
        sa.text(
            """
        INSERT INTO tiers (tier_name, monthly_price, included_quota, overage_rate, api_keys_limit, features, created_at)
        VALUES ('custom', NULL, NULL, 2.00, NULL,
                '["all"]'::jsonb,
                CURRENT_TIMESTAMP)
        ON CONFLICT (tier_name) DO UPDATE SET
            overage_rate = 2.00
    """
        )
    )

    # 5. Initialize quota for existing users
    connection.execute(
        sa.text(
            """
        UPDATE users u
        SET
            quota_balance = t.included_quota,
            quota_reset_date = DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
        FROM tiers t
        WHERE u.tier_id = t.id
    """
        )
    )

    # 6. Create initial quota transaction records for existing users
    connection.execute(
        sa.text(
            """
        INSERT INTO quota_transactions (user_id, transaction_type, amount, balance_before, balance_after, description)
        SELECT
            u.id,
            'quota_reset',
            t.included_quota,
            0.00,
            t.included_quota,
            'Initial quota allocation (migration)'
        FROM users u
        JOIN tiers t ON u.tier_id = t.id
        WHERE t.included_quota > 0
    """
        )
    )

    print("✅ Migration to quota-based pricing completed successfully")


def downgrade():

    """Downgrade from quota-based pricing"""

    # Remove quota tracking from users
    op.drop_column("users", "total_overage_charges")
    op.drop_column("users", "quota_reset_date")
    op.drop_column("users", "quota_balance")

    # Drop quota transactions table
    op.drop_index("idx_quota_transactions_created", "quota_transactions")
    op.drop_index("idx_quota_transactions_user", "quota_transactions")
    op.drop_table("quota_transactions")

    # Remove new columns from tiers
    op.drop_column("tiers", "single_sms_rate")
    op.drop_column("tiers", "overage_rate")
    op.drop_column("tiers", "included_quota")

    # Revert tier prices (optional - adjust as needed)
    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
        UPDATE tiers SET monthly_price = 29.00 WHERE tier_name = 'starter';
        UPDATE tiers SET monthly_price = 99.00 WHERE tier_name = 'professional';
        DELETE FROM tiers WHERE tier_name IN ('turbo', 'pro', 'custom');
    """
        )
    )

    print("⚠️ Downgraded from quota-based pricing")