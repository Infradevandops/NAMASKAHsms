#!/bin/bash
# Render.com build script - runs migrations automatically

echo "🔧 Running database migrations..."

# Run the idempotency fix
python scripts/fix_production_idempotency.py

# Run any pending Alembic migrations
# alembic upgrade head

echo "✅ Migrations complete"
