#!/usr/bin/env python3
"""Create test admin user."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from app.core.database import get_db
from app.models.user import User
import bcrypt
from datetime import datetime

def create_admin():
    """Create admin user."""
    try:
        db = next(get_db())
        
        # Check if admin exists
        admin = db.query(User).filter(User.email == "admin@namaskah.app").first()
        if admin:
            print("Admin user already exists")
            return
        
        # Create admin
        password_hash = bcrypt.hashpw(
            "admin123".encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        
        admin = User(
            email="admin@namaskah.app",
            username="admin",
            password_hash=password_hash,
            is_active=True,
            credits=1000.0,
            created_at=datetime.utcnow()
        )
        
        db.add(admin)
        db.commit()
        
        print("✅ Admin user created:")
        print("   Email: admin@namaskah.app")
        print("   Password: admin123")
        
    except Exception as e:
        print(f"❌ Error creating admin: {e}")

if __name__ == "__main__":
    create_admin()