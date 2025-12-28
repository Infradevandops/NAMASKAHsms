#!/usr/bin/env python3
"""
Deployment Verification Script
Checks all critical issues before deployment
"""
import os
import sys
from pathlib import Path

def check_notification_model():
    """Verify Notification model inherits from BaseModel."""
    notification_file = Path("app/models/notification.py")
    if not notification_file.exists():
        return False, "notification.py not found"
    
    content = notification_file.read_text()
    if "class Notification(BaseModel):" in content:
        return True, "✅ Notification model correctly inherits from BaseModel"
    elif "class Notification(Base):" in content:
        return False, "❌ Notification model still inherits from Base (needs BaseModel)"
    else:
        return False, "❌ Cannot determine Notification model inheritance"

def check_alembic_config():
    """Verify alembic.ini exists."""
    alembic_file = Path("alembic.ini")
    if alembic_file.exists():
        return True, "✅ alembic.ini found"
    return False, "❌ alembic.ini not found"

def check_env_keys():
    """Check if environment has secure keys."""
    issues = []
    
    # Check .env files
    env_files = [".env", ".env.production", ".env.local"]
    found_env = False
    
    for env_file in env_files:
        env_path = Path(env_file)
        if env_path.exists():
            found_env = True
            content = env_path.read_text()
            
            # Check for weak keys
            if "SECRET_KEY=" in content:
                if any(weak in content for weak in ["your-", "change-me", "placeholder", "SECRET_KEY=\n", "SECRET_KEY="]):
                    issues.append(f"⚠️  {env_file} has weak SECRET_KEY")
            
            if "JWT_SECRET_KEY=" in content:
                if any(weak in content for weak in ["your-", "change-me", "placeholder", "JWT_SECRET_KEY=\n", "JWT_SECRET_KEY="]):
                    issues.append(f"⚠️  {env_file} has weak JWT_SECRET_KEY")
    
    if not found_env:
        return False, "❌ No .env files found"
    
    if issues:
        return False, "\n".join(issues)
    
    return True, "✅ Environment keys configured"

def check_database_url():
    """Check database configuration."""
    env_files = [".env.production", ".env"]
    
    for env_file in env_files:
        env_path = Path(env_file)
        if env_path.exists():
            content = env_path.read_text()
            if "DATABASE_URL=" in content:
                if "postgresql://" in content:
                    return True, "✅ PostgreSQL database configured"
                elif "sqlite://" in content and "production" in env_file:
                    return False, "⚠️  SQLite not recommended for production"
    
    return None, "ℹ️  Database URL not found in .env files"

def main():
    """Run all checks."""
    print("=" * 70)
    print("NAMASKAH DEPLOYMENT VERIFICATION")
    print("=" * 70)
    print()
    
    checks = [
        ("Notification Model", check_notification_model),
        ("Alembic Configuration", check_alembic_config),
        ("Environment Keys", check_env_keys),
        ("Database Configuration", check_database_url),
    ]
    
    all_passed = True
    
    for name, check_func in checks:
        passed, message = check_func()
        print(f"{name}:")
        print(f"  {message}")
        print()
        
        if passed is False:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("✅ ALL CHECKS PASSED - Ready for deployment!")
        print("=" * 70)
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Fix issues before deployment")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Fix the Notification model (already done if you ran the fix)")
        print("2. Generate secure keys: python3 scripts/generate_secure_keys.py")
        print("3. Update production environment variables with secure keys")
        print("4. Ensure PostgreSQL is configured for production")
        return 1

if __name__ == "__main__":
    sys.exit(main())
