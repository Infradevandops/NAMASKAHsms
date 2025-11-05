"""Add Google OAuth fields

Revision ID: 006_add_google_oauth
Revises: 0320b211ff27
Create Date: 2024-11-04 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '006_add_google_oauth'
down_revision = '0320b211ff27'
branch_labels = None
depends_on = None

def upgrade():
    # Add Google OAuth fields to users table
    op.add_column('users', sa.Column('google_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('provider', sa.String(50), nullable=False, server_default='email'))
    op.add_column('users', sa.Column('avatar_url', sa.String(500), nullable=True))
    
    # Make password_hash nullable for OAuth users
    op.alter_column('users', 'password_hash', nullable=True)
    
    # Create index for Google ID lookups
    op.create_index('ix_users_google_id', 'users', ['google_id'])
    op.create_index('ix_users_provider', 'users', ['provider'])

def downgrade():
    op.drop_index('ix_users_provider', 'users')
    op.drop_index('ix_users_google_id', 'users')
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'provider')
    op.drop_column('users', 'google_id')