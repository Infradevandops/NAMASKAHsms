#!/bin/bash

# Start Namaskah SMS Server

echo "🚀 Starting Namaskah SMS Server..."
echo ""

# Check if port 8000 is already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port 8000 is already in use. Killing existing process..."
    lsof -ti:8000 | xargs kill -9
    sleep 2
fi

# Start the server
echo "📡 Starting FastAPI server on http://localhost:8000"
echo ""

python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

echo ""
echo "✅ Server started successfully!"
echo "📍 Open: http://localhost:8000"
echo "🔐 Login: admin@namaskah.app / admin123"
