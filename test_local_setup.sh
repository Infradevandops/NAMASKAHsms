#!/bin/bash
# Quick Local Testing Setup Script

echo "🚀 Setting up local testing environment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Setup local environment
if [ ! -f ".env.local" ]; then
    echo "⚙️  Creating local environment file..."
    cat > .env.local << EOF
# Local Testing Environment
DATABASE_URL=sqlite:///./test_sms.db
BASE_URL=http://localhost:8000
ENVIRONMENT=development
DEBUG=true

# Security Keys (for testing only)
SECRET_KEY=test_secret_key_32_chars_minimum_length
JWT_SECRET_KEY=test_jwt_secret_key_32_chars_minimum_length

# Test API Keys (demo mode)
FIVESIM_API_KEY=test_key
PAYSTACK_SECRET_KEY=sk_test_demo
PAYSTACK_PUBLIC_KEY=pk_test_demo
EOF
fi

# Copy local env for testing
cp .env.local .env

# Run database migrations
echo "🗄️  Setting up database..."
alembic upgrade head

# Create test admin user
echo "👤 Creating test admin user..."
python3 -c "
import asyncio
from sqlalchemy.orm import Session
from app.core.database import engine, get_db
from app.models.user import User
from app.utils.security import hash_password

def create_test_admin():
    db = Session(engine)
    
    # Check if admin exists
    admin = db.query(User).filter(User.email == 'admin@test.com').first()
    if not admin:
        admin = User(
            email='admin@test.com',
            hashed_password=hash_password('admin123'),
            full_name='Test Admin',
            is_active=True,
            is_admin=True,
            credits=100.0,
            free_verifications=10
        )
        db.add(admin)
        db.commit()
        print('✅ Test admin created: admin@test.com / admin123')
    else:
        print('✅ Test admin already exists')
    
    db.close()

create_test_admin()
"

echo "✅ Local setup complete!"
echo ""
echo "🚀 To start testing:"
echo "1. Start server: uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo "2. Run tests: python test_verification_flow.py"
echo "3. Open browser: http://localhost:8000"
echo ""
echo "📊 Test credentials:"
echo "   Email: admin@test.com"
echo "   Password: admin123"