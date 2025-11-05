#!/bin/bash
# Local Testing Script

echo "🚀 Starting Local Development Server..."

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the application
uvicorn main:app --reload --host 0.0.0.0 --port 8000