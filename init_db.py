#!/usr/bin/env python3
"""Initialize database with all tables"""

from app.core.database import engine
from app.models.base import Base

# Import all models to ensure they're registered

def init_database():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()