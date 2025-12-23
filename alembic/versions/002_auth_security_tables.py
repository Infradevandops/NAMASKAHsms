"""Add authentication security tables."""
from alembic import op
import sqlalchemy as sa

revision = '002_auth_security'
down_revision = 'a828e54f0016'
branch_labels = None
depends_on = None

def upgrade():
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()
    
    if 'login_attempts' not in existing_tables:
        op.create_table(
        'login_attempts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
        op.create_index(op.f('ix_login_attempts_email'), 'login_attempts', ['email'], unique=False)
        op.create_index(op.f('ix_login_attempts_timestamp'), 'login_attempts', ['timestamp'], unique=False)

    if 'auth_audit_logs' not in existing_tables:
        op.create_table(
        'auth_audit_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('event_type', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('details', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
        op.create_index(op.f('ix_auth_audit_logs_user_id'), 'auth_audit_logs', ['user_id'], unique=False)
        op.create_index(op.f('ix_auth_audit_logs_timestamp'), 'auth_audit_logs', ['timestamp'], unique=False)

    if 'account_lockouts' not in existing_tables:
        op.create_table(
        'account_lockouts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
        op.create_index(op.f('ix_account_lockouts_email'), 'account_lockouts', ['email'], unique=True)

def downgrade():
    op.drop_index(op.f('ix_account_lockouts_email'), table_name='account_lockouts')
    op.drop_table('account_lockouts')
    op.drop_index(op.f('ix_auth_audit_logs_timestamp'), table_name='auth_audit_logs')
    op.drop_index(op.f('ix_auth_audit_logs_user_id'), table_name='auth_audit_logs')
    op.drop_table('auth_audit_logs')
    op.drop_index(op.f('ix_login_attempts_timestamp'), table_name='login_attempts')
    op.drop_index(op.f('ix_login_attempts_email'), table_name='login_attempts')
    op.drop_table('login_attempts')
