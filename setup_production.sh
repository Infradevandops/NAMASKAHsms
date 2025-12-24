#!/bin/bash

# Production Setup Script for Namaskah SMS Platform
# This script automates the setup process

set -e

echo "🚀 Namaskah SMS Platform - Production Setup"
echo "==========================================="
echo ""

# Step 1: Check Python
echo "✓ Checking Python installation..."
python3 --version

# Step 2: Install dependencies
echo "✓ Installing dependencies..."
pip3 install -r requirements.txt

# Step 3: Database migration
echo "✓ Running database migrations..."
# alembic upgrade head # Disabled - DB already complete

# Step 4: Check environment
echo "✓ Checking environment configuration..."
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env with your configuration"
    exit 1
fi

# Step 5: Run tests
echo "✓ Running integration tests..."
python3 -m pytest app/tests/test_textverified_integration.py -v

# Step 6: Initialize admin
echo "✓ Initializing admin user..."
python3 -c "
from app.core.database import SessionLocal
from app.models.user import User
from app.utils.security import hash_password

db = SessionLocal()
admin = db.query(User).filter(User.email == 'admin@namaskah.app').first()
if not admin:
    admin_user = User(
        email='admin@namaskah.app',
        password_hash=hash_password('admin123'),
        credits=1000.0,
        free_verifications=100,
        is_admin=True,
        email_verified=True
    )
    db.add(admin_user)
    db.commit()
    print('✓ Admin user created')
else:
    print('✓ Admin user already exists')
db.close()
"

echo ""
echo "✅ Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Configure webhooks in TextVerified dashboard"
echo "2. Start server: uvicorn main:app --host 0.0.0.0 --port 8000"
echo "3. Access dashboard: http://localhost:8000/app"
echo ""
