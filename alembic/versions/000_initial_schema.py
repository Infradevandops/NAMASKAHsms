"""initial_schema

Revision ID: 000_initial_schema
Revises: 
Create Date: 2026-04-16 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '000_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Import models to get metadata
    from app.models.base import Base
    from app.models import user, verification, transaction, subscription_tier
    
    # Create all tables from metadata
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    # Drop all tables
    from app.models.base import Base
    from app.models import user, verification, transaction, subscription_tier
    
    Base.metadata.drop_all(bind=op.get_bind())
