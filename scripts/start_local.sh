#!/bin/bash

# Start Vrenum with Local Database
echo "🚀 Starting Vrenum API (Local Development)..."
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Creating..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Use local development environment
export ENVIRONMENT=development
export DATABASE_URL=sqlite:///./data/vrenum_local.db

echo "✅ Environment: development"
echo "✅ Database: SQLite (./data/vrenum_local.db)"
echo ""

# Skip migrations for SQLite (they're for PostgreSQL)
echo "⏭️  Skipping migrations (SQLite database)..."
echo ""

# Start the application
echo "🌐 Starting server on http://localhost:8000"
echo "📝 Press Ctrl+C to stop"
echo ""

uvicorn main:app --host 127.0.0.1 --port 8000 --reload
