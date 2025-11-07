#!/bin/bash
echo "🚀 Starting Namaskah SMS..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from example..."
    cp .env.example .env
    echo "📝 Please edit .env with your credentials"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
# shellcheck source=.venv/bin/activate
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Create default users if database doesn't exist
if [ ! -f sms.db ]; then
    echo "👤 Creating default users..."
    python create_users.py
fi

# Start server
HOST=${HOST:-127.0.0.1}
PORT=${PORT:-8000}
echo "✅ Starting server on http://${HOST}:${PORT}"
echo ""
echo "📝 Login with:"
echo "   Email: admin@namaskah.app"
echo "   Password: admin123"
echo ""
uvicorn main:app --host "$HOST" --port "$PORT" --reload
