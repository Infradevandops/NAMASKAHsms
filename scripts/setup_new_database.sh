#!/bin/bash
# Setup script for new Render database
# Run this after updating DATABASE_URL in Render dashboard

set -e

echo "🔧 Setting up new database..."

# New database connection
export DATABASE_URL="postgresql://namaskahdb:MscldS0AaA5Sszn4nG6wgpuVlFJSw3QI@dpg-d6p9bm3h46gs73816e30-a/namaskahdb_olby"

echo "✅ Database URL configured"

# Run migrations
echo "📦 Running Alembic migrations..."
alembic upgrade head

echo "✅ Migrations complete"

# Create initial admin user (optional)
echo "👤 Creating admin user..."
python -c "
from app.core.database import SessionLocal
from app.models.user import User
from passlib.context import CryptContext
import uuid

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
db = SessionLocal()

# Check if admin exists
admin = db.query(User).filter(User.email == 'admin@namaskah.app').first()
if not admin:
    admin = User(
        id=str(uuid.uuid4()),
        email='admin@namaskah.app',
        username='admin',
        hashed_password=pwd_context.hash('changeme123'),
        is_active=True,
        is_verified=True,
        subscription_tier='custom',
        credits=1000.0
    )
    db.add(admin)
    db.commit()
    print('✅ Admin user created: admin@namaskah.app / changeme123')
else:
    print('ℹ️  Admin user already exists')

db.close()
"

echo "✅ Database setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Update DATABASE_URL in Render dashboard"
echo "2. Trigger manual deploy"
echo "3. Login with: admin@namaskah.app / changeme123"
echo "4. Change password immediately!"
