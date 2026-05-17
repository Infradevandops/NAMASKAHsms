#!/bin/bash
echo "🔄 Restarting Vrenum..."

# Kill existing processes
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "python.*start_with_fallback.py" 2>/dev/null
sleep 2

# Export correct database
export DATABASE_URL=postgresql://machine@localhost:5432/vrenum_sms

# Start server
echo "✅ Starting on http://127.0.0.1:8001"
./start.sh
