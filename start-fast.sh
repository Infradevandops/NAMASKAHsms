#!/bin/bash
echo "🚀 Starting Namaskah SMS (Fast Mode)..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ No .env file found. Creating from example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your credentials"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Smart dependency installation - only install if needed
REQUIREMENTS_HASH=$(md5 -q requirements.txt 2>/dev/null || md5sum requirements.txt | cut -d' ' -f1)
INSTALLED_HASH_FILE=".venv/.requirements_hash"

if [ ! -f "$INSTALLED_HASH_FILE" ] || [ "$(cat $INSTALLED_HASH_FILE)" != "$REQUIREMENTS_HASH" ]; then
    echo "📦 Installing/updating dependencies..."
    if pip install -q -r requirements.txt; then
        echo "$REQUIREMENTS_HASH" > "$INSTALLED_HASH_FILE"
        echo "✅ Dependencies installed"
    else
        echo "❌ Failed to install dependencies"
        exit 1
    fi
else
    echo "✅ Dependencies already up to date (skipping install)"
fi

# Run database migrations (skip if fails - may already be applied)
echo "🗄️  Running database migrations..."
alembic upgrade head 2>/dev/null || echo "ℹ️  Migrations skipped (may already be applied)"

# Clean up existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "uvicorn main:app" 2>/dev/null || true
sleep 1

# Find available port
HOST=${HOST:-127.0.0.1}
PORT=${PORT:-8000}

# Check if port is in use and find alternative
while lsof -i:$PORT >/dev/null 2>&1; do
    PORT=$((PORT + 1))
    if [ $PORT -gt 8010 ]; then
        echo "❌ No available ports found between 8000-8010"
        exit 1
    fi
done

echo ""
echo "✅ Server starting on http://${HOST}:${PORT}"
echo "📱 Landing: http://${HOST}:${PORT}"
echo "📋 Dashboard: http://${HOST}:${PORT}/dashboard"
echo "✉️  Verify: http://${HOST}:${PORT}/verify"
echo ""
echo "Press Ctrl+C to stop"
echo ""

uvicorn main:app --host "$HOST" --port "$PORT" --reload
