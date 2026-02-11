#!/bin/bash
echo "🔄 Restarting with correct database..."

# Kill all server processes
pkill -9 -f "uvicorn main:app" 2>/dev/null
pkill -9 -f "start_with_fallback" 2>/dev/null
sleep 2

# Force correct database
export DATABASE_URL="postgresql://machine@localhost:5432/namaskah_db"

# Start server
cd "$(dirname "$0")"
python3 -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload
