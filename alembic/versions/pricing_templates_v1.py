"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

Add Pricing Templates System

Revision ID: pricing_templates_v1
Created: 2025-12-25
"""


revision = "pricing_templates_v1"
down_revision = "quota_pricing_v3_1"
branch_labels = None
depends_on = None


def upgrade():

    """Create pricing templates tables"""

    # 1. Create pricing_templates table
    op.create_table(
        "pricing_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="false"),
        sa.Column("region", sa.String(10), server_default="US"),
        sa.Column("currency", sa.String(3), server_default="USD"),
        sa.Column(
            "created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("effective_date", sa.TIMESTAMP(), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("idx_pricing_templates_active", "pricing_templates", ["is_active"])
    op.create_index("idx_pricing_templates_region", "pricing_templates", ["region"])

    # 2. Create tier_pricing table
    op.create_table(
        "tier_pricing",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("tier_name", sa.String(50), nullable=False),
        sa.Column("monthly_price", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("included_quota", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("overage_rate", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("features", postgresql.JSONB(), nullable=True),
        sa.Column("api_keys_limit", sa.Integer(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["template_id"], ["pricing_templates.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_id", "tier_name", name="uq_template_tier"),
    )

    op.create_index("idx_tier_pricing_template", "tier_pricing", ["template_id"])

    # 3. Create pricing_history table
    op.create_table(
        "pricing_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("previous_template_id", sa.Integer(), nullable=True),
        sa.Column("changed_by", sa.Integer(), nullable=True),
        sa.Column(
            "changed_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(
            ["template_id"], ["pricing_templates.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("idx_pricing_history_template", "pricing_history", ["template_id"])
    op.create_index("idx_pricing_history_changed_at", "pricing_history", ["changed_at"])

    # 4. Create user_pricing_assignments table (for A/B testing)
    op.create_table(
        "user_pricing_assignments",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column(
            "assigned_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("assigned_by", sa.String(50), server_default="auto"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["template_id"], ["pricing_templates.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )

    # 5. Insert default templates
    connection = op.get_bind()

    # Template 1: Standard Pricing (Active)
    connection.execute(
        sa.text(
            """
        INSERT INTO pricing_templates (name, description, is_active, region, currency)
        VALUES ('Standard Pricing', 'Current production pricing for US market', true, 'US', 'USD')
    """
        )
    )

    template_id = connection.execute(
        sa.text("SELECT id FROM pricing_templates WHERE name = 'Standard Pricing'")
    ).scalar()

    connection.execute(
        sa.text(
            """
        INSERT INTO tier_pricing (template_id, tier_name, monthly_price, included_quota, overage_rate, display_order, features)
        VALUES
            ({template_id}, 'payg_trial', 0.00, 0.00, 2.50, 1, '{{"api_access": false}}'::jsonb),
            ({template_id}, 'starter', 8.99, 5.00, 0.50, 2, '{{"api_access": true, "api_keys_limit": 5, "area_code_selection": true}}'::jsonb),
            ({template_id}, 'pro', 25.00, 15.00, 0.30, 3, '{{"api_access": true, "api_keys_limit": 10, "area_code_selection": true, "isp_filtering": true}}'::jsonb),
            ({template_id}, 'custom', 35.00, 25.00, 0.20, 4, '{{"api_access": true, "api_keys_limit": null, "area_code_selection": true, "isp_filtering": true, "dedicated_support": true}}'::jsonb)
    """
        )
    )

    # Template 2: Holiday Sale (Inactive)
    connection.execute(
        sa.text(
            """
        INSERT INTO pricing_templates (name, description, is_active, region, currency, effective_date, expires_at)
        VALUES ('Holiday Sale', '20% off all plans - Holiday promotion', false, 'US', 'USD', '2025-12-20', '2026-01-05')
    """
        )
    )

    template_id = connection.execute(
        sa.text("SELECT id FROM pricing_templates WHERE name = 'Holiday Sale'")
    ).scalar()

    connection.execute(
        sa.text(
            """
        INSERT INTO tier_pricing (template_id, tier_name, monthly_price, included_quota, overage_rate, display_order, features)
        VALUES
            ({template_id}, 'payg_trial', 0.00, 0.00, 2.50, 1, '{{"api_access": false}}'::jsonb),
            ({template_id}, 'starter', 7.19, 5.00, 0.50, 2, '{{"api_access": true, "api_keys_limit": 5, "area_code_selection": true}}'::jsonb),
            ({template_id}, 'pro', 20.00, 15.00, 0.30, 3, '{{"api_access": true, "api_keys_limit": 10, "area_code_selection": true, "isp_filtering": true}}'::jsonb),
            ({template_id}, 'custom', 28.00, 25.00, 0.20, 4, '{{"api_access": true, "api_keys_limit": null, "area_code_selection": true, "isp_filtering": true, "dedicated_support": true}}'::jsonb)
    """
        )
    )

    # Template 3: EU Pricing (Inactive)
    connection.execute(
        sa.text(
            """
        INSERT INTO pricing_templates (name, description, is_active, region, currency)
        VALUES ('EU Pricing', 'Standard pricing for European market with VAT', false, 'EU', 'EUR')
    """
        )
    )

    template_id = connection.execute(
        sa.text("SELECT id FROM pricing_templates WHERE name = 'EU Pricing'")
    ).scalar()

    connection.execute(
        sa.text(
            """
        INSERT INTO tier_pricing (template_id, tier_name, monthly_price, included_quota, overage_rate, display_order, features)
        VALUES
            ({template_id}, 'payg_trial', 0.00, 0.00, 2.30, 1, '{{"api_access": false}}'::jsonb),
            ({template_id}, 'starter', 8.49, 5.00, 0.45, 2, '{{"api_access": true, "api_keys_limit": 5, "area_code_selection": true}}'::jsonb),
            ({template_id}, 'pro', 23.00, 15.00, 0.28, 3, '{{"api_access": true, "api_keys_limit": 10, "area_code_selection": true, "isp_filtering": true}}'::jsonb),
            ({template_id}, 'custom', 32.00, 25.00, 0.18, 4, '{{"api_access": true, "api_keys_limit": null, "area_code_selection": true, "isp_filtering": true, "dedicated_support": true}}'::jsonb)
    """
        )
    )

    # Template 4: Test Pricing (Inactive)
    connection.execute(
        sa.text(
            """
        INSERT INTO pricing_templates (name, description, is_active, region, currency, metadata)
        VALUES ('Test Pricing', 'A/B testing template - experimental pricing', false, 'US', 'USD', '{"ab_test": true, "test_group": "A"}'::jsonb)
    """
        )
    )

    template_id = connection.execute(
        sa.text("SELECT id FROM pricing_templates WHERE name = 'Test Pricing'")
    ).scalar()

    connection.execute(
        sa.text(
            """
        INSERT INTO tier_pricing (template_id, tier_name, monthly_price, included_quota, overage_rate, display_order, features)
        VALUES
            ({template_id}, 'payg_trial', 0.00, 0.00, 2.50, 1, '{{"api_access": false}}'::jsonb),
            ({template_id}, 'starter', 9.99, 6.00, 0.45, 2, '{{"api_access": true, "api_keys_limit": 5, "area_code_selection": true}}'::jsonb),
            ({template_id}, 'pro', 27.00, 18.00, 0.28, 3, '{{"api_access": true, "api_keys_limit": 10, "area_code_selection": true, "isp_filtering": true}}'::jsonb),
            ({template_id}, 'custom', 39.00, 30.00, 0.18, 4, '{{"api_access": true, "api_keys_limit": null, "area_code_selection": true, "isp_filtering": true, "dedicated_support": true}}'::jsonb)
    """
        )
    )

    print("✅ Created 4 pricing templates:")
    print("   1. Standard Pricing (Active)")
    print("   2. Holiday Sale (Inactive)")
    print("   3. EU Pricing (Inactive)")
    print("   4. Test Pricing (Inactive)")


def downgrade():

    """Remove pricing templates tables"""
    op.drop_table("user_pricing_assignments")
    op.drop_table("pricing_history")
    op.drop_table("tier_pricing")
    op.drop_table("pricing_templates")

    print("⚠️ Removed pricing templates system")