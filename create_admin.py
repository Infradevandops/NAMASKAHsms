#!/usr/bin/env python3
"""Create admin user for Namaskah SMS platform."""

from app.core.database import SessionLocal
from app.models.user import User
from app.utils.security import hash_password

def create_admin_user():
    """Create or update admin user."""
    db = SessionLocal()
    
    try:
        admin_email = "admin@namaskah.app"
        admin_password = "NamaskahAdmin2024!"
        
        # Check if admin exists
        admin = db.query(User).filter(User.email == admin_email).first()
        if admin:
            # Update existing admin
            admin.password_hash = hash_password(admin_password)
            admin.is_admin = True
            admin.email_verified = True
            admin.credits = 1000.0
            admin.free_verifications = 100
            db.commit()
            print("✅ Admin user updated successfully!")
        else:
            # Create new admin user
            admin_user = User(
                email=admin_email,
                password_hash=hash_password(admin_password),
                credits=1000.0,
                free_verifications=100,
                is_admin=True,
                email_verified=True
            )
            db.add(admin_user)
            db.commit()
            print("✅ Admin user created successfully!")
        
        print(f"📧 Email: {admin_email}")
        print(f"🔑 Password: {admin_password}")
        print("💰 Credits: 1000.0")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()
