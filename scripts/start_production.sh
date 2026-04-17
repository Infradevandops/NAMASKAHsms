#!/bin/bash
# Render startup script - initializes database and runs migrations

set -e

echo "🚀 Starting Namaskah SMS..."

# Initialize database schema if needed
echo "📊 Initializing database schema..."
python -c "
from app.core.database import Base, engine
from app.models import user, verification, transaction, subscription_tier
print('Creating tables...')
Base.metadata.create_all(bind=engine)
print('✅ Database schema ready')
"

# Run migrations
echo "🔄 Running migrations..."
alembic upgrade head || echo "⚠️ Migrations skipped or failed"

# Start application
echo "✅ Starting application..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WORKERS:-2}
