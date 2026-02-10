#!/bin/bash
# Local development startup script - Always uses port 9876

PORT=9876
HOST="0.0.0.0"

echo "🚀 Starting Namaskah on port $PORT"

# Kill any existing process on this port
lsof -ti:$PORT | xargs kill -9 2>/dev/null
sleep 1

# Start the app
uvicorn main:app --host $HOST --port $PORT --reload
