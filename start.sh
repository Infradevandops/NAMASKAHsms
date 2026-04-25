#!/bin/bash
set -e

echo "Starting Namaskah SMS API..."

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application with Gunicorn
echo "Starting Gunicorn server..."
exec gunicorn main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT:-8000} \
    --timeout 120 \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
