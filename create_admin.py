#!/usr/bin/env python3
"""Create admin user with credits for testing."""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_admin_user():
    """Create admin user with testing credits."""
    try:
        from app.core.database import SessionLocal
        from app.models.user import User
        from app.utils.security import hash_password
        
        db = SessionLocal()
        
        # Admin credentials
        admin_email = "admin@namaskah.app"
        admin_password = "NamaskahAdmin2024!"
        
        # Check if admin exists
        admin = db.query(User).filter(User.email == admin_email).first()
        
        if admin:
            print("✅ Admin user already exists")
            print(f"Email: {admin_email}")
            print(f"Password: {admin_password}")
            print(f"Credits: {admin.credits}")
            return
        
        # Create admin user
        admin_user = User(
            email=admin_email,
            password_hash=hash_password(admin_password),
            credits=1000.0,
            is_admin=True,
            email_verified=True
        )
        
        db.add(admin_user)
        db.commit()
        
        print("✅ Admin user created successfully!")
        print(f"Email: {admin_email}")
        print(f"Password: {admin_password}")
        print("Credits: 1000.0")
        print("Admin: Yes")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔑 Production Login Credentials:")
        print("Email: admin@namaskah.app")
        print("Password: NamaskahAdmin2024!")
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    create_admin_user()