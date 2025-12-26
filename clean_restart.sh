#!/bin/bash

# Clean Restart Script - Fixes cache and port issues

echo "🧹 Cleaning Python cache..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
find . -name "*.pyo" -delete 2>/dev/null

echo "🔪 Killing port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null

echo "⏳ Waiting for port to free..."
sleep 2

echo "🚀 Starting server..."
./server.sh start

echo ""
echo "✅ Clean restart complete!"
echo "   Visit: http://localhost:8000"
