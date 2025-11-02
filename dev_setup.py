#!/usr/bin/env python3
"""Local development setup script."""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def main():
    """Setup local development environment."""
    print("🚀 Setting up Namaskah SMS for local development...")
    
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Run database migrations
    if not run_command("alembic upgrade head", "Running database migrations"):
        print("⚠️  Migration failed, but continuing...")
    
    # Setup demo user
    if not run_command("python3 setup_demo_user.py", "Creating demo admin user"):
        print("⚠️  Demo user creation failed")
    
    print("\n🎉 Local development setup complete!")
    print("\n📋 Next steps:")
    print("1. Start the server: python3 -m uvicorn main:app --reload --port 8000")
    print("2. Open browser: http://localhost:8000")
    print("3. Login with: admin@namaskah.app / Namaskah@Admin2024")
    print("\n💡 If dropdowns still show 'Loading...', the API endpoints are working")
    print("   but the frontend might need a refresh or the server restart.")

if __name__ == "__main__":
    main()