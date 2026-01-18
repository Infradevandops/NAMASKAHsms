#!/bin/bash
# Ultra-fast startup - skips dependency check entirely
# Use this when you know dependencies are already installed

echo "🚀 Starting Namaskah SMS (Ultra-Fast Mode)..."

# Activate virtual environment
source .venv/bin/activate

# Clean up existing processes
pkill -f "uvicorn main:app" 2>/dev/null || true

# Find available port
HOST=${HOST:-127.0.0.1}
PORT=${PORT:-8000}

while lsof -i:$PORT >/dev/null 2>&1; do
    PORT=$((PORT + 1))
    if [ $PORT -gt 8010 ]; then
        echo "❌ No available ports found"
        exit 1
    fi
done

echo "✅ Starting server on http://${HOST}:${PORT}"
echo "📱 Landing: http://${HOST}:${PORT}"
echo "📋 Dashboard: http://${HOST}:${PORT}/dashboard"
echo ""

uvicorn main:app --host "$HOST" --port "$PORT" --reload
