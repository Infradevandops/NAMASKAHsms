"""Add SMS message model for inbox storage.

Revision ID: add_sms_message_model
Revises: 
Create Date: 2024-12-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_sms_message_model'
down_revision = '001_consolidated'  # After base schema
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create SMS message table."""
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Skip if table already exists
    if 'sms_messages' in inspector.get_table_names():
        print("⚠️  sms_messages table already exists, skipping")
        return
    
    # Check if rentals table exists for foreign key
    has_rentals = 'rentals' in inspector.get_table_names()
    
    op.create_table(
        'sms_messages',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('rental_id', sa.String(36), nullable=True),
        sa.Column('from_number', sa.String(20), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('external_id', sa.String(100), nullable=True),
        sa.Column('received_at', sa.DateTime(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_id'),
    )
    
    # Only add rental foreign key if rentals table exists
    if has_rentals:
        op.create_foreign_key(
            'fk_sms_messages_rental_id',
            'sms_messages', 'rentals',
            ['rental_id'], ['id']
        )
    
    # Create indexes for performance
    op.create_index('ix_sms_messages_user_id', 'sms_messages', ['user_id'])
    op.create_index('ix_sms_messages_is_read', 'sms_messages', ['is_read'])
    op.create_index('ix_sms_messages_received_at', 'sms_messages', ['received_at'])


def downgrade() -> None:
    """Drop SMS message table."""
    op.drop_index('ix_sms_messages_received_at', table_name='sms_messages')
    op.drop_index('ix_sms_messages_is_read', table_name='sms_messages')
    op.drop_index('ix_sms_messages_user_id', table_name='sms_messages')
    op.drop_table('sms_messages')
