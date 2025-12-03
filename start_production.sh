#!/bin/bash
# Production startup script with validation

set -e

echo "🚀 Starting Namaskah SMS Production Server"
echo "=========================================="

# Check environment
if [ ! -f ".env.production" ]; then
    echo "❌ .env.production not found"
    exit 1
fi

# Load environment
export $(cat .env.production | grep -v '^#' | xargs)

# Validate critical variables
if [ -z "$SECRET_KEY" ] || [ -z "$JWT_SECRET_KEY" ] || [ -z "$DATABASE_URL" ]; then
    echo "❌ Missing critical environment variables"
    exit 1
fi

echo "✅ Environment variables loaded"

# Run validation script
echo ""
echo "Running production validation..."
python3 scripts/validate_production.py

if [ $? -ne 0 ]; then
    echo "❌ Validation failed"
    exit 1
fi

echo ""
echo "✅ All validations passed"
echo ""

# Apply database migrations
echo "Applying database migrations..."
alembic upgrade head

if [ $? -ne 0 ]; then
    echo "⚠️  Migration warning (may be normal if already up to date)"
fi

echo ""
echo "🎯 Starting Uvicorn server..."
echo "=========================================="

# Check if we can connect to database before running migrations
if psql $DATABASE_URL -c "SELECT 1" &>/dev/null; then
    echo "Database accessible, applying migrations..."
    alembic upgrade head
else
    echo "⚠️  Database not accessible (expected if running locally)"
    echo "Skipping migrations - they will run in production"
fi

echo ""

# Start Uvicorn with production settings
uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --loop uvloop \
    --http httptools \
    --access-log \
    --log-level info
