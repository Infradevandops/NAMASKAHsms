"""initial_schema
 
Revision ID: 000_initial_schema
Revises: 
Create Date: 2026-04-16 14:00:00.000000
 
"""
from alembic import op
import sqlalchemy as sa
 
revision = '000_initial_schema'
down_revision = None
branch_labels = None
depends_on = None
 
def upgrade() -> None:
    # 1. Import all models to ensure metadata is fully populated
    # This captures the entire schema as it exists in the current code
    from app.models.base import Base
    import app.models  # This imports the __init__.py which aggregates all models
    
    # 2. Get connection and check if we are in a fresh environment
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()
    
    # 3. Create all tables from metadata if they don't exist
    # Note: In SQLite, create_all handles existence checks. 
    # In Postgres, it will only create missing tables.
    Base.metadata.create_all(bind=bind)
 
def downgrade() -> None:
    # Downgrade is not practical for a "create_all" base
    pass
