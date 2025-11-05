"""Add KYC system tables

Revision ID: 007_add_kyc_system
Revises: 83868cab20af
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '007_add_kyc_system'
down_revision = '83868cab20af'
branch_labels = None
depends_on = None


def upgrade():
    """Add KYC system tables."""
    
    # KYC Profiles table
    op.create_table('kyc_profiles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('verification_level', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('phone_number', sa.String(), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('nationality', sa.String(), nullable=True),
        sa.Column('address_line1', sa.String(), nullable=True),
        sa.Column('address_line2', sa.String(), nullable=True),
        sa.Column('city', sa.String(), nullable=True),
        sa.Column('state', sa.String(), nullable=True),
        sa.Column('postal_code', sa.String(), nullable=True),
        sa.Column('country', sa.String(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('rejected_at', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('aml_status', sa.String(), nullable=True),
        sa.Column('pep_status', sa.Boolean(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kyc_profiles_user_id'), 'kyc_profiles', ['user_id'], unique=True)
    op.create_index(op.f('ix_kyc_profiles_status'), 'kyc_profiles', ['status'], unique=False)
    
    # KYC Documents table
    op.create_table('kyc_documents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('kyc_profile_id', sa.String(), nullable=False),
        sa.Column('document_type', sa.String(), nullable=False),
        sa.Column('document_number', sa.String(), nullable=True),
        sa.Column('document_expiry', sa.Date(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('file_name', sa.String(), nullable=True),
        sa.Column('file_size', sa.Float(), nullable=True),
        sa.Column('file_hash', sa.String(), nullable=True),
        sa.Column('mime_type', sa.String(), nullable=True),
        sa.Column('verification_status', sa.String(), nullable=False),
        sa.Column('verification_method', sa.String(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('extracted_data', sa.JSON(), nullable=True),
        sa.Column('ocr_text', sa.Text(), nullable=True),
        sa.Column('is_encrypted', sa.Boolean(), nullable=True),
        sa.Column('access_count', sa.Float(), nullable=True),
        sa.Column('last_accessed', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kyc_documents_kyc_profile_id'), 'kyc_documents', ['kyc_profile_id'], unique=False)
    op.create_index(op.f('ix_kyc_documents_file_hash'), 'kyc_documents', ['file_hash'], unique=True)
    
    # KYC Verification Limits table
    op.create_table('kyc_verification_limits',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('verification_level', sa.String(), nullable=False),
        sa.Column('daily_limit', sa.Float(), nullable=False),
        sa.Column('monthly_limit', sa.Float(), nullable=False),
        sa.Column('annual_limit', sa.Float(), nullable=False),
        sa.Column('allowed_services', sa.JSON(), nullable=True),
        sa.Column('max_transaction_amount', sa.Float(), nullable=True),
        sa.Column('requires_additional_auth', sa.Boolean(), nullable=True),
        sa.Column('country_restrictions', sa.JSON(), nullable=True),
        sa.Column('service_restrictions', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kyc_verification_limits_verification_level'), 'kyc_verification_limits', ['verification_level'], unique=True)
    
    # KYC Audit Logs table
    op.create_table('kyc_audit_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('old_status', sa.String(), nullable=True),
        sa.Column('new_status', sa.String(), nullable=True),
        sa.Column('old_level', sa.String(), nullable=True),
        sa.Column('new_level', sa.String(), nullable=True),
        sa.Column('admin_id', sa.String(), nullable=True),
        sa.Column('system_action', sa.Boolean(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kyc_audit_logs_user_id'), 'kyc_audit_logs', ['user_id'], unique=False)
    
    # AML Screening table
    op.create_table('aml_screenings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('kyc_profile_id', sa.String(), nullable=False),
        sa.Column('screening_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('match_score', sa.Float(), nullable=True),
        sa.Column('matches_found', sa.JSON(), nullable=True),
        sa.Column('search_terms', sa.JSON(), nullable=True),
        sa.Column('data_sources', sa.JSON(), nullable=True),
        sa.Column('screening_provider', sa.String(), nullable=True),
        sa.Column('reviewed_by', sa.String(), nullable=True),
        sa.Column('review_decision', sa.String(), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_aml_screenings_kyc_profile_id'), 'aml_screenings', ['kyc_profile_id'], unique=False)
    
    # KYC Settings table
    op.create_table('kyc_settings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('setting_key', sa.String(), nullable=False),
        sa.Column('setting_value', sa.JSON(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kyc_settings_setting_key'), 'kyc_settings', ['setting_key'], unique=True)
    
    # Biometric Verification table
    op.create_table('biometric_verifications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('kyc_profile_id', sa.String(), nullable=False),
        sa.Column('verification_type', sa.String(), nullable=False),
        sa.Column('reference_image_path', sa.String(), nullable=True),
        sa.Column('verification_image_path', sa.String(), nullable=True),
        sa.Column('match_score', sa.Float(), nullable=True),
        sa.Column('liveness_score', sa.Float(), nullable=True),
        sa.Column('verification_result', sa.String(), nullable=True),
        sa.Column('confidence_level', sa.String(), nullable=True),
        sa.Column('algorithm_used', sa.String(), nullable=True),
        sa.Column('processing_time', sa.Float(), nullable=True),
        sa.Column('quality_scores', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_biometric_verifications_kyc_profile_id'), 'biometric_verifications', ['kyc_profile_id'], unique=False)
    
    # Insert default KYC limits
    op.execute("""
        INSERT INTO kyc_verification_limits (id, verification_level, daily_limit, monthly_limit, annual_limit, allowed_services, requires_additional_auth, created_at, updated_at)
        VALUES 
        ('limit_unverified', 'unverified', 10.0, 50.0, 200.0, '["basic"]', 0, datetime('now'), datetime('now')),
        ('limit_basic', 'basic', 100.0, 500.0, 2000.0, '["basic", "premium"]', 0, datetime('now'), datetime('now')),
        ('limit_enhanced', 'enhanced', 1000.0, 5000.0, 20000.0, '["basic", "premium", "enterprise"]', 0, datetime('now'), datetime('now')),
        ('limit_premium', 'premium', 10000.0, 50000.0, 200000.0, '["all"]', 1, datetime('now'), datetime('now'))
    """)
    
    # Insert default KYC settings
    op.execute("""
        INSERT INTO kyc_settings (id, setting_key, setting_value, description, is_active, created_at, updated_at)
        VALUES 
        ('setting_auto_verify', 'auto_verify_threshold', '0.8', 'Confidence threshold for automatic verification', 1, datetime('now'), datetime('now')),
        ('setting_require_selfie', 'require_selfie', 'true', 'Require selfie for all KYC submissions', 1, datetime('now'), datetime('now')),
        ('setting_aml_enabled', 'aml_screening_enabled', 'true', 'Enable automatic AML screening', 1, datetime('now'), datetime('now')),
        ('setting_retention', 'document_retention_days', '2555', 'Document retention period in days (7 years)', 1, datetime('now'), datetime('now'))
    """)


def downgrade():
    """Remove KYC system tables."""
    op.drop_table('biometric_verifications')
    op.drop_table('kyc_settings')
    op.drop_table('aml_screenings')
    op.drop_table('kyc_audit_logs')
    op.drop_table('kyc_verification_limits')
    op.drop_table('kyc_documents')
    op.drop_table('kyc_profiles')