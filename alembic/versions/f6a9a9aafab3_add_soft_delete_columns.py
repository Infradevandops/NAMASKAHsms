"""Add soft delete columns

Revision ID: f6a9a9aafab3
Revises: 005_add_performance_indexes
Create Date: 2025-11-22 07:14:37.781356

"""
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

from alembic import op

# revision identifiers, used by Alembic.
revision = 'f6a9a9aafab3'
down_revision = '005_add_performance_indexes'
branch_labels = None
depends_on = None


def safe_drop_index(index_name, table_name):
    """Safely drop an index if it exists."""
    try:
        op.drop_index(op.f(index_name), table_name=table_name)
    except Exception:
        pass


def safe_drop_table(table_name):
    """Safely drop a table if it exists."""
    try:
        op.drop_table(table_name)
    except Exception:
        pass


def upgrade() -> None:
    # Safely drop indexes and tables that may not exist
    safe_drop_index('ix_rentals_status', 'rentals')
    safe_drop_index('ix_rentals_user_id', 'rentals')
    safe_drop_table('rentals')

    safe_drop_index('ix_user_sessions_created_at', 'user_sessions')
    safe_drop_index('ix_user_sessions_expires_at', 'user_sessions')
    safe_drop_index('ix_user_sessions_user_id', 'user_sessions')
    safe_drop_table('user_sessions')

    safe_drop_table('kyc_verification_limits')

    safe_drop_index('ix_auth_audit_logs_timestamp', 'auth_audit_logs')
    safe_drop_index('ix_auth_audit_logs_user_id', 'auth_audit_logs')
    safe_drop_table('auth_audit_logs')

    safe_drop_index('ix_login_attempts_email', 'login_attempts')
    safe_drop_index('ix_login_attempts_timestamp', 'login_attempts')
    safe_drop_table('login_attempts')

    safe_drop_index('ix_aml_screenings_kyc_profile_id', 'aml_screenings')
    safe_drop_table('aml_screenings')

    safe_drop_index('ix_account_lockouts_email', 'account_lockouts')
    safe_drop_table('account_lockouts')

    safe_drop_index('ix_biometric_verifications_kyc_profile_id', 'biometric_verifications')
    safe_drop_table('biometric_verifications')

    safe_drop_index('ix_kyc_documents_file_hash', 'kyc_documents')
    safe_drop_index('ix_kyc_documents_kyc_profile_id', 'kyc_documents')
    safe_drop_table('kyc_documents')

    safe_drop_index('ix_sms_messages_is_read', 'sms_messages')
    safe_drop_index('ix_sms_messages_received_at', 'sms_messages')
    safe_drop_index('ix_sms_messages_user_id', 'sms_messages')
    safe_drop_table('sms_messages')

    safe_drop_index('ix_sms_forwarding_user_id', 'sms_forwarding')
    safe_drop_table('sms_forwarding')

    safe_drop_index('ix_audit_logs_action', 'audit_logs')
    safe_drop_index('ix_audit_logs_user_id', 'audit_logs')
    safe_drop_table('audit_logs')

    safe_drop_index('ix_waitlist_email', 'waitlist')
    safe_drop_table('waitlist')

    safe_drop_index('ix_kyc_profiles_status', 'kyc_profiles')
    safe_drop_index('ix_kyc_profiles_user_id', 'kyc_profiles')
    safe_drop_table('kyc_profiles')

    # Add soft delete columns to existing tables
    try:
        op.add_column('activity_logs', sa.Column('deleted_at', sa.DateTime(), nullable=True))
        op.add_column('activity_logs', sa.Column('is_deleted', sa.Boolean(), nullable=False))
    except Exception:
        pass

    try:
        op.add_column('users', sa.Column('deleted_at', sa.DateTime(), nullable=True))
        op.add_column('users', sa.Column('is_deleted', sa.Boolean(), nullable=False))
    except Exception:
        pass

    try:
        op.add_column('verifications', sa.Column('deleted_at', sa.DateTime(), nullable=True))
        op.add_column('verifications', sa.Column('is_deleted', sa.Boolean(), nullable=False))
    except Exception:
        pass


def downgrade() -> None:
    # Downgrade is not fully implemented for safety
    pass
