"""Add user event tracking tables for analytics.

Revision ID: add_user_events_analytics
Revises: 794eda6caa30
Create Date: 2026-05-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_user_events_analytics'
down_revision = '794eda6caa30'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_events table if it doesn't exist
    if not op.get_context().dialect.has_table(op.get_context().bind, 'user_events'):
        op.create_table(
            'user_events',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('user_id', sa.String(36), nullable=False),
            sa.Column('event_type', sa.String(50), nullable=False),
            sa.Column('event_data', sa.JSON(), nullable=True),
            sa.Column('ip_address', sa.String(45), nullable=True),
            sa.Column('user_agent', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_user_event_type', 'user_events', ['user_id', 'event_type'])
        op.create_index('idx_event_created', 'user_events', ['event_type', 'created_at'])
        op.create_index('ix_user_events_user_id', 'user_events', ['user_id'])
        op.create_index('ix_user_events_event_type', 'user_events', ['event_type'])
        op.create_index('ix_user_events_created_at', 'user_events', ['created_at'])

    # Create daily_user_snapshots table if it doesn't exist
    if not op.get_context().dialect.has_table(op.get_context().bind, 'daily_user_snapshots'):
        op.create_table(
            'daily_user_snapshots',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('snapshot_date', sa.Date(), nullable=False),
            sa.Column('total_users', sa.Integer(), nullable=True),
            sa.Column('active_users', sa.Integer(), nullable=True),
            sa.Column('new_users', sa.Integer(), nullable=True),
            sa.Column('churned_users', sa.Integer(), nullable=True),
            sa.Column('total_revenue', sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column('total_verifications', sa.Integer(), nullable=True),
            sa.Column('avg_verification_cost', sa.Numeric(precision=8, scale=2), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('snapshot_date', name='uq_daily_snapshot_date')
        )
        op.create_index('ix_daily_snapshots_date', 'daily_user_snapshots', ['snapshot_date'])

    # Create feature_usage table if it doesn't exist
    if not op.get_context().dialect.has_table(op.get_context().bind, 'feature_usage'):
        op.create_table(
            'feature_usage',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('user_id', sa.String(36), nullable=False),
            sa.Column('feature_name', sa.String(100), nullable=False),
            sa.Column('usage_count', sa.Integer(), nullable=True, server_default='1'),
            sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_feature_usage_user_id', 'feature_usage', ['user_id'])
        op.create_index('ix_feature_usage_feature_name', 'feature_usage', ['feature_name'])

    # Create admin_alerts table if it doesn't exist
    if not op.get_context().dialect.has_table(op.get_context().bind, 'admin_alerts'):
        op.create_table(
            'admin_alerts',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('alert_type', sa.String(50), nullable=False),
            sa.Column('severity', sa.String(20), nullable=False),
            sa.Column('title', sa.String(255), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('event_data', sa.JSON(), nullable=True),
            sa.Column('is_resolved', sa.Boolean(), nullable=True, server_default='false'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_admin_alerts_type', 'admin_alerts', ['alert_type'])
        op.create_index('ix_admin_alerts_severity', 'admin_alerts', ['severity'])
        op.create_index('ix_admin_alerts_resolved', 'admin_alerts', ['is_resolved'])


def downgrade() -> None:
    op.drop_index('ix_admin_alerts_resolved', table_name='admin_alerts')
    op.drop_index('ix_admin_alerts_severity', table_name='admin_alerts')
    op.drop_index('ix_admin_alerts_type', table_name='admin_alerts')
    op.drop_table('admin_alerts')

    op.drop_index('ix_feature_usage_feature_name', table_name='feature_usage')
    op.drop_index('ix_feature_usage_user_id', table_name='feature_usage')
    op.drop_table('feature_usage')

    op.drop_index('ix_daily_snapshots_date', table_name='daily_user_snapshots')
    op.drop_table('daily_user_snapshots')

    op.drop_index('ix_user_events_created_at', table_name='user_events')
    op.drop_index('ix_user_events_event_type', table_name='user_events')
    op.drop_index('ix_user_events_user_id', table_name='user_events')
    op.drop_index('idx_event_created', table_name='user_events')
    op.drop_index('idx_user_event_type', table_name='user_events')
    op.drop_table('user_events')
