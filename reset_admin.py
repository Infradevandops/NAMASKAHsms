#!/usr/bin/env python3
"""Reset admin password - Use this to set/reset admin credentials"""

import sys
from app.core.database import SessionLocal
from app.models.user import User
from app.utils.security import hash_password

def reset_admin_password(email: str, new_password: str):
    """Reset admin password"""
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == email).first()
        
        if not admin:
            print(f"❌ User {email} not found")
            print("\nAvailable users:")
            users = db.query(User).all()
            for u in users:
                print(f"  - {u.email} (admin={u.is_admin})")
            return False
        
        # Update password and ensure admin privileges
        admin.password_hash = hash_password(new_password)
        admin.is_admin = True
        admin.email_verified = True
        admin.subscription_tier = 'turbo'
        
        db.commit()
        
        print(f"✅ Admin password reset successful!")
        print(f"\n📧 Email: {email}")
        print(f"🔑 Password: {new_password}")
        print(f"👑 Tier: {admin.subscription_tier}")
        print(f"💰 Credits: {admin.credits}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🔐 Admin Password Reset Tool\n")
    
    if len(sys.argv) == 3:
        email = sys.argv[1]
        password = sys.argv[2]
    else:
        email = input("Admin email [admin@namaskah.app]: ").strip() or "admin@namaskah.app"
        password = input("New password: ").strip()
        
        if not password:
            print("❌ Password cannot be empty")
            sys.exit(1)
    
    reset_admin_password(email, password)
