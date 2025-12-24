"""Consolidated initial schema - replaces fragmented migrations

Revision ID: 001_consolidated
Revises: 
Create Date: 2024-01-20 10:00:00.000000

This migration consolidates 001-013 into a single clean schema.
"""
import sqlalchemy as sa
from alembic import op

revision = "001_consolidated"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables with proper schema."""
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Skip if tables already exist (production database)
    if 'users' in inspector.get_table_names():
        print("⚠️  Tables already exist, skipping consolidated migration")
        return

    # Users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("is_admin", sa.Boolean(), default=False),
        sa.Column("email_verified", sa.Boolean(), default=False),
        sa.Column("credits", sa.Float(), default=0.0),
        sa.Column("free_verifications", sa.Float(), default=0.0),
        sa.Column("verification_token", sa.String(255), nullable=True),
        sa.Column("reset_token", sa.String(255), nullable=True),
        sa.Column("reset_token_expires", sa.DateTime(timezone=True), nullable=True),
        sa.Column("referral_code", sa.String(50), nullable=True, unique=True),
        sa.Column("referred_by", sa.String(255), nullable=True),
        sa.Column("referral_earnings", sa.Float(), default=0.0),
        sa.Column("google_id", sa.String(255), nullable=True, unique=True),
        sa.Column("provider", sa.String(50), default="email"),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("mfa_secret", sa.String(32), nullable=True),
        sa.Column("mfa_enabled", sa.Boolean(), default=False),
        sa.Column("affiliate_id", sa.String(50), nullable=True),
        sa.Column("partner_type", sa.String(50), nullable=True),
        sa.Column("commission_tier", sa.String(50), nullable=True),
        sa.Column("is_affiliate", sa.Boolean(), default=False),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_google_id", "users", ["google_id"])
    op.create_index("ix_users_referral_code", "users", ["referral_code"])
    op.create_index("ix_users_provider", "users", ["provider"])

    # API Keys table
    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("prefix", sa.String(10), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("last_used", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_api_keys_user_id", "api_keys", ["user_id"])

    # Verifications table
    op.create_table(
        "verifications",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("service_name", sa.String(100), nullable=False),
        sa.Column("phone_number", sa.String(20), nullable=True),
        sa.Column("capability", sa.String(10), nullable=True),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("verification_code", sa.String(20), nullable=True),
        sa.Column("cost", sa.Float(), nullable=False),
        sa.Column("call_duration", sa.Float(), nullable=True),
        sa.Column("transcription", sa.Text(), nullable=True),
        sa.Column("audio_url", sa.String(500), nullable=True),
        sa.Column("requested_carrier", sa.String(50), nullable=True),
        sa.Column("requested_area_code", sa.String(10), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("country", sa.String(3), default="US"),
        sa.Column("provider", sa.String(20), default="5sim"),
        sa.Column("operator", sa.String(50), nullable=True),
        sa.Column("pricing_tier", sa.String(20), default="standard"),
        sa.Column("activation_id", sa.BigInteger(), nullable=True),
        sa.Column("sms_text", sa.Text(), nullable=True),
        sa.Column("sms_code", sa.String(20), nullable=True),
        sa.Column("sms_received_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_verifications_user_id", "verifications", ["user_id"])
    op.create_index("ix_verifications_service_name", "verifications", ["service_name"])
    op.create_index("ix_verifications_status", "verifications", ["status"])
    op.create_index("ix_verifications_provider", "verifications", ["provider"])
    op.create_index("ix_verifications_activation_id", "verifications", ["activation_id"])

    # Rentals table
    op.create_table(
        "rentals",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("phone_number", sa.String(20), nullable=False),
        sa.Column("service_name", sa.String(50), nullable=False),
        sa.Column("country_code", sa.String(3), nullable=False),
        sa.Column("provider", sa.String(20), default="5sim"),
        sa.Column("activation_id", sa.String(50), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), default="active"),
        sa.Column("cost", sa.Numeric(10, 4), nullable=False),
        sa.Column("duration_hours", sa.Integer(), default=24),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_rentals_user_id", "rentals", ["user_id"])
    op.create_index("ix_rentals_status", "rentals", ["status"])

    # Transactions table
    op.create_table(
        "transactions",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])
    op.create_index("ix_transactions_type", "transactions", ["type"])

    # Support Tickets table
    op.create_table(
        "support_tickets",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", sa.String(36), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), default="open"),
        sa.Column("admin_response", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_support_tickets_user_id", "support_tickets", ["user_id"])
    op.create_index("ix_support_tickets_status", "support_tickets", ["status"])

    # Audit Logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("user_id", sa.String(36), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])

    # KYC Profiles table
    op.create_table(
        "kyc_profiles",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False, unique=True),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("verification_level", sa.String(20), default="unverified"),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("phone_number", sa.String(20), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("nationality", sa.String(3), nullable=True),
        sa.Column("address_line1", sa.String(255), nullable=True),
        sa.Column("address_line2", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("country", sa.String(3), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("risk_score", sa.Float(), default=0.0),
        sa.Column("aml_status", sa.String(20), nullable=True),
        sa.Column("pep_status", sa.Boolean(), default=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("verification_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_kyc_profiles_user_id", "kyc_profiles", ["user_id"])
    op.create_index("ix_kyc_profiles_status", "kyc_profiles", ["status"])

    # KYC Documents table
    op.create_table(
        "kyc_documents",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("kyc_profile_id", sa.String(36), nullable=False),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("document_number", sa.String(100), nullable=True),
        sa.Column("document_expiry", sa.Date(), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column("file_size", sa.Float(), nullable=True),
        sa.Column("file_hash", sa.String(64), nullable=True, unique=True),
        sa.Column("mime_type", sa.String(50), nullable=True),
        sa.Column("verification_status", sa.String(20), default="pending"),
        sa.Column("verification_method", sa.String(50), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("extracted_data", sa.JSON(), nullable=True),
        sa.Column("ocr_text", sa.Text(), nullable=True),
        sa.Column("is_encrypted", sa.Boolean(), default=False),
        sa.Column("access_count", sa.Integer(), default=0),
        sa.Column("last_accessed", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["kyc_profile_id"], ["kyc_profiles.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_kyc_documents_kyc_profile_id", "kyc_documents", ["kyc_profile_id"])
    op.create_index("ix_kyc_documents_file_hash", "kyc_documents", ["file_hash"])

    # KYC Verification Limits table
    op.create_table(
        "kyc_verification_limits",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("verification_level", sa.String(20), nullable=False, unique=True),
        sa.Column("daily_limit", sa.Float(), nullable=False),
        sa.Column("monthly_limit", sa.Float(), nullable=False),
        sa.Column("annual_limit", sa.Float(), nullable=False),
        sa.Column("allowed_services", sa.JSON(), nullable=True),
        sa.Column("max_transaction_amount", sa.Float(), nullable=True),
        sa.Column("requires_additional_auth", sa.Boolean(), default=False),
        sa.Column("country_restrictions", sa.JSON(), nullable=True),
        sa.Column("service_restrictions", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # AML Screenings table
    op.create_table(
        "aml_screenings",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("kyc_profile_id", sa.String(36), nullable=False),
        sa.Column("screening_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("match_score", sa.Float(), nullable=True),
        sa.Column("matches_found", sa.JSON(), nullable=True),
        sa.Column("search_terms", sa.JSON(), nullable=True),
        sa.Column("data_sources", sa.JSON(), nullable=True),
        sa.Column("screening_provider", sa.String(50), nullable=True),
        sa.Column("reviewed_by", sa.String(36), nullable=True),
        sa.Column("review_decision", sa.String(20), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["kyc_profile_id"], ["kyc_profiles.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_aml_screenings_kyc_profile_id", "aml_screenings", ["kyc_profile_id"])

    # Biometric Verifications table
    op.create_table(
        "biometric_verifications",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("kyc_profile_id", sa.String(36), nullable=False),
        sa.Column("verification_type", sa.String(50), nullable=False),
        sa.Column("reference_image_path", sa.String(500), nullable=True),
        sa.Column("verification_image_path", sa.String(500), nullable=True),
        sa.Column("match_score", sa.Float(), nullable=True),
        sa.Column("liveness_score", sa.Float(), nullable=True),
        sa.Column("verification_result", sa.String(20), nullable=True),
        sa.Column("confidence_level", sa.String(20), nullable=True),
        sa.Column("algorithm_used", sa.String(100), nullable=True),
        sa.Column("processing_time", sa.Float(), nullable=True),
        sa.Column("quality_scores", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["kyc_profile_id"], ["kyc_profiles.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_biometric_verifications_kyc_profile_id", "biometric_verifications", ["kyc_profile_id"])

    # Waitlist table
    op.create_table(
        "waitlist",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("is_notified", sa.Boolean(), default=False),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_waitlist_email", "waitlist", ["email"])

    # Whitelabel Configs table
    op.create_table(
        "whitelabel_configs",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("domain", sa.String(255), nullable=False, unique=True),
        sa.Column("company_name", sa.String(100), nullable=False),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("primary_color", sa.String(7), nullable=True),
        sa.Column("secondary_color", sa.String(7), nullable=True),
        sa.Column("custom_css", sa.Text(), nullable=True),
        sa.Column("api_subdomain", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("features", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_whitelabel_configs_domain", "whitelabel_configs", ["domain"])

    # Enterprise Tiers table
    op.create_table(
        "enterprise_tiers",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("min_monthly_spend", sa.Float(), nullable=False),
        sa.Column("sla_uptime", sa.Float(), nullable=True),
        sa.Column("max_response_time", sa.Integer(), nullable=True),
        sa.Column("priority_support", sa.Boolean(), default=False),
        sa.Column("dedicated_manager", sa.Boolean(), default=False),
        sa.Column("custom_rates", sa.JSON(), nullable=True),
        sa.Column("features", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_enterprise_tiers_name", "enterprise_tiers", ["name"])

    # Enterprise Accounts table
    op.create_table(
        "enterprise_accounts",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("tier_id", sa.String(36), nullable=False),
        sa.Column("account_manager_email", sa.String(255), nullable=True),
        sa.Column("monthly_spend", sa.Float(), default=0.0),
        sa.Column("sla_credits", sa.Float(), default=0.0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tier_id"], ["enterprise_tiers.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_enterprise_accounts_user_id", "enterprise_accounts", ["user_id"])

    # Affiliate Programs table
    op.create_table(
        "affiliate_programs",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("program_type", sa.String(50), nullable=False),
        sa.Column("commission_rate", sa.Float(), nullable=False),
        sa.Column("tier_requirements", sa.JSON(), nullable=True),
        sa.Column("features", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Affiliate Applications table
    op.create_table(
        "affiliate_applications",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("program_type", sa.String(50), nullable=False),
        sa.Column("program_options", sa.JSON(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_affiliate_applications_email", "affiliate_applications", ["email"])

    # Affiliate Commissions table
    op.create_table(
        "affiliate_commissions",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("affiliate_id", sa.String(36), nullable=False),
        sa.Column("transaction_id", sa.String(255), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("commission_rate", sa.Float(), nullable=False),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("payout_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["affiliate_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_affiliate_commissions_affiliate_id", "affiliate_commissions", ["affiliate_id"])
    op.create_index("ix_affiliate_commissions_status", "affiliate_commissions", ["status"])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("affiliate_commissions")
    op.drop_table("affiliate_applications")
    op.drop_table("affiliate_programs")
    op.drop_table("enterprise_accounts")
    op.drop_table("enterprise_tiers")
    op.drop_table("whitelabel_configs")
    op.drop_table("waitlist")
    op.drop_table("biometric_verifications")
    op.drop_table("aml_screenings")
    op.drop_table("kyc_verification_limits")
    op.drop_table("kyc_documents")
    op.drop_table("kyc_profiles")
    op.drop_table("audit_logs")
    op.drop_table("support_tickets")
    op.drop_table("transactions")
    op.drop_table("rentals")
    op.drop_table("verifications")
    op.drop_table("api_keys")
    op.drop_table("users")
