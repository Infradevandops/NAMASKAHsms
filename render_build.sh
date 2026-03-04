#!/bin/bash
set -e
# Render.com build script - runs migrations automatically

echo "🔧 Running database migrations..."
alembic upgrade head
echo "✅ Migrations complete"
