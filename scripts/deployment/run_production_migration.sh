#!/bin/bash
# Production Database Migration Script
# Run this to apply pending migrations to production database

set -e  # Exit on error

echo "🔄 Starting database migration..."
echo "================================"

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable is not set"
    echo "Please set it to your production database URL"
    exit 1
fi

echo "✓ Database URL configured"

# Run Alembic migrations
echo ""
echo "📊 Running Alembic migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Migration completed successfully!"
    echo "================================"
    echo ""
    echo "Next steps:"
    echo "1. Restart your application"
    echo "2. Test login functionality"
    echo "3. Verify all features are working"
else
    echo ""
    echo "❌ Migration failed!"
    echo "Please check the error messages above"
    exit 1
fi
