#!/bin/bash
# Production start script for Render
# Handles fresh database initialization gracefully

set -e

echo "🚀 Starting Namaskah API..."

# Wait for database to be ready
echo "⏳ Waiting for database..."
python -c "
import time
import sys
from sqlalchemy import create_engine, text
import os

db_url = os.getenv('DATABASE_URL')
if not db_url:
    print('❌ DATABASE_URL not set')
    sys.exit(1)

engine = create_engine(db_url)
max_retries = 30
retry_delay = 2

for i in range(max_retries):
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('✅ Database is ready')
        break
    except Exception as e:
        if i == max_retries - 1:
            print(f'❌ Database connection failed after {max_retries} attempts')
            sys.exit(1)
        print(f'⏳ Waiting for database... ({i+1}/{max_retries})')
        time.sleep(retry_delay)
"

# Run Alembic migrations
echo "📦 Running database migrations..."
# Check for multiple heads and merge if needed
if alembic heads | grep -q "(head)"; then
    HEAD_COUNT=$(alembic heads | grep -c "(head)")
    if [ "$HEAD_COUNT" -gt 1 ]; then
        echo "⚠️  Multiple migration heads detected, using merge migration..."
        alembic upgrade 061d9956377d || {
            echo "⚠️  Migration failed, attempting to initialize database..."
            python -c "
from app.core.database import Base, engine
Base.metadata.create_all(bind=engine)
print('✅ Database tables created')
"
            alembic stamp 061d9956377d
            echo "✅ Database initialized"
        }
    else
        alembic upgrade head || {
            echo "⚠️  Migration failed, attempting to initialize database..."
            python -c "
from app.core.database import Base, engine
Base.metadata.create_all(bind=engine)
print('✅ Database tables created')
"
            alembic stamp head
            echo "✅ Database initialized"
        }
    fi
else
    alembic upgrade head || {
        echo "⚠️  Migration failed, attempting to initialize database..."
        python -c "
from app.core.database import Base, engine
Base.metadata.create_all(bind=engine)
print('✅ Database tables created')
"
        alembic stamp head
        echo "✅ Database initialized"
    }
fi

# Start the application
echo "🎯 Starting Gunicorn..."
exec gunicorn main:app \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${WEB_CONCURRENCY:-1} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
