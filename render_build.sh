#!/bin/bash
set -e
# Render.com build script - runs migrations automatically

echo "🔧 Creating base tables..."
python -c "
from app.core.database import engine
from app.models.user import Base
Base.metadata.create_all(bind=engine)
print('Base tables created')
"

echo "🔧 Running database migrations..."
alembic upgrade head
echo "✅ Migrations complete"
