"""Add SMS forwarding model.

Revision ID: add_sms_forwarding_model
Revises: add_sms_message_model
Create Date: 2024-12-01 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'add_sms_forwarding_model'
down_revision = 'add_sms_message_model'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create SMS forwarding table."""
    op.create_table(
        'sms_forwarding',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('rental_id', sa.String(36), nullable=True),
        sa.Column('phone_number', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('telegram_id', sa.String(100), nullable=True),
        sa.Column('phone_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('email_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('telegram_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['rental_id'], ['rentals.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_sms_forwarding_user_id', 'sms_forwarding', ['user_id'])


def downgrade() -> None:
    """Drop SMS forwarding table."""
    op.drop_index('ix_sms_forwarding_user_id', table_name='sms_forwarding')
    op.drop_table('sms_forwarding')
