#!/usr/bin/env python3
"""
Database initialization script for Namaskah SMS Platform
Ensures all tables exist and creates admin user
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import create_tables, SessionLocal
from app.models.user import User
from app.utils.security import hash_password

def init_database():
    """Initialize database with tables and admin user."""
    print("🚀 Initializing Namaskah SMS Database...")
    
    try:
        # Create all tables
        print("📊 Creating database tables...")
        create_tables()
        print("✅ Database tables created successfully")
        
        # Create admin user
        print("👤 Creating admin user...")
        db = SessionLocal()
        
        try:
            # Check if admin exists
            admin = db.query(User).filter(User.email == "admin@namaskah.app").first()
            if admin:
                print("✅ Admin user already exists")
                print(f"📧 Email: {admin.email}")
                print(f"🔑 Admin status: {admin.is_admin}")
                print(f"💰 Credits: {admin.credits}")
            else:
                # Create admin user with both possible passwords
                admin_user = User(
                    email="admin@namaskah.app",
                    password_hash=hash_password("admin123"),
                    credits=1000.0,
                    free_verifications=100,
                    is_admin=True,
                    email_verified=True
                )
                
                db.add(admin_user)
                db.commit()
                
                print("✅ Admin user created successfully!")
                print("📧 Email: admin@namaskah.app")
                print("🔑 Password: admin123")
                print("💰 Credits: 1000.0")
                print("🎯 Free verifications: 100")
                
                # Also create user with alternative password
                admin_user_alt = User(
                    email="admin@namaskah.com",
                    password_hash=hash_password("NamaskahAdmin2024!"),
                    credits=1000.0,
                    free_verifications=100,
                    is_admin=True,
                    email_verified=True
                )
                
                db.add(admin_user_alt)
                db.commit()
                print("✅ Alternative admin user created: admin@namaskah.com / NamaskahAdmin2024!")
                
        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            db.rollback()
        finally:
            db.close()
            
        print("\n🎉 Database initialization completed successfully!")
        print("\n📋 Login Credentials:")
        print("   Email: admin@namaskah.app")
        print("   Password: admin123")
        print("   OR")
        print("   Email: admin@namaskah.com")
        print("   Password: NamaskahAdmin2024!")
        print("\n🌐 Access the application at: http://localhost:8000/auth/login")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_database()