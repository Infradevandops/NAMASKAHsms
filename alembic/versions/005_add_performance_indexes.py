"""Add performance indexes for frequently queried columns.

Revision ID: 005_add_performance_indexes
Revises: 004_add_moderator_role
Create Date: 2025-11-21 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '005_add_performance_indexes'
down_revision = '004_add_moderator_role'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_index('ix_users_created_at', 'users', ['created_at'], if_not_exists=True)
    op.create_index('ix_verifications_created_at', 'verifications', ['created_at'], if_not_exists=True)
    op.create_index('ix_verifications_status', 'verifications', ['status'], if_not_exists=True)
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'], if_not_exists=True)
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'], if_not_exists=True)

def downgrade() -> None:
    op.drop_index('ix_audit_logs_user_id', 'audit_logs')
    op.drop_index('ix_audit_logs_created_at', 'audit_logs')
    op.drop_index('ix_verifications_status', 'verifications')
    op.drop_index('ix_verifications_created_at', 'verifications')
    op.drop_index('ix_users_created_at', 'users')
