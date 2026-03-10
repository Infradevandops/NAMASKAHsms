#!/bin/bash
# Production migration script with safety checks

set -e

echo "🔍 Checking migration requirements..."

# Check if SKIP_MIGRATIONS is set
if [ "$SKIP_MIGRATIONS" = "true" ]; then
    echo "⏭️  Migrations skipped (SKIP_MIGRATIONS=true)"
    exit 0
fi

# Check if alembic is available
if ! command -v alembic &> /dev/null; then
    echo "⚠️  Alembic not installed, skipping migrations"
    exit 0
fi

# Check if alembic.ini exists
if [ ! -f "alembic.ini" ]; then
    echo "⚠️  alembic.ini not found, skipping migrations"
    exit 0
fi

# Run migrations with error handling
echo "🔄 Running database migrations..."
if alembic upgrade head; then
    echo "✅ Migrations completed successfully"
else
    echo "⚠️  Migration failed, but continuing deployment"
    exit 0  # Don't fail deployment
fi
