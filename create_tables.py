#!/usr/bin/env python3
"""Create missing database tables."""

import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def create_missing_tables():
    """Create any missing database tables."""
    try:
        from app.core.database import create_tables

        create_tables()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        sys.exit(1)


if __name__ == "__main__":
    create_missing_tables()
