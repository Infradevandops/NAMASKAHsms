#!/bin/bash
echo "Starting Namaskah SMS..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "No .env file found. Creating from example..."
    cp .env.example .env
    echo "Please edit .env with your credentials"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
# shellcheck source=/dev/null
source .venv/bin/activate

# Smart dependency installation - only install if requirements changed
REQUIREMENTS_HASH=$(md5 -q requirements.txt 2>/dev/null || md5sum requirements.txt | cut -d' ' -f1)
INSTALLED_HASH_FILE=".venv/.requirements_hash"

if [ ! -f "$INSTALLED_HASH_FILE" ] || [ "$(cat $INSTALLED_HASH_FILE)" != "$REQUIREMENTS_HASH" ]; then
    echo "Installing dependencies..."
    # Add timeout to prevent hanging
    if timeout 120 pip install -q -r requirements.txt; then
        echo "$REQUIREMENTS_HASH" > "$INSTALLED_HASH_FILE"
        echo "✅ Dependencies installed successfully"
    else
        echo "⚠️  Dependency installation timed out or failed"
        echo "💡 Try: ./start-now.sh (skips dependency check)"
        exit 1
    fi
else
    echo "✅ Dependencies already installed (skipping)"
fi

# Run database migrations (skip if fails - may already be applied)
echo "Running database migrations..."
alembic upgrade head 2>/dev/null || echo "Note: Migrations skipped (may already be applied)"

# Clean up existing processes
echo "Cleaning up existing processes..."
pkill -f "uvicorn main:app" 2>/dev/null || true

# Find available port
HOST=${HOST:-127.0.0.1}
PORT=${PORT:-8000}

# Check if port is in use and find alternative
while lsof -i:$PORT >/dev/null 2>&1; do
    PORT=$((PORT + 1))
    if [ $PORT -gt 8010 ]; then
        echo "No available ports found between 8000-8010"
        exit 1
    fi
done

echo "Starting server on http://${HOST}:${PORT}"
echo "📱 Landing: http://${HOST}:${PORT}"
echo "📋 Dashboard: http://${HOST}:${PORT}/dashboard"
echo "✉️ Verify: http://${HOST}:${PORT}/verify"
echo ""
uvicorn main:app --host "$HOST" --port "$PORT" --reload
