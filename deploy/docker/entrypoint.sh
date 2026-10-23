#!/bin/bash
set -e

echo "🚀 Starting VRENUM SMS..."

# Wait for database to be ready
echo "⏳ Waiting for database..."
while ! pg_isready -h db -U ${POSTGRES_USER:-vrenum} -q 2>/dev/null; do
    sleep 1
done
echo "✅ Database is ready"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis..."
while ! redis-cli -h redis ping > /dev/null 2>&1; do
    sleep 1
done
echo "✅ Redis is ready"

# Run database migrations
echo "🔄 Running database migrations..."
alembic upgrade head
echo "✅ Migrations complete"

# Start the application
echo "🎯 Starting application..."
exec "$@"
