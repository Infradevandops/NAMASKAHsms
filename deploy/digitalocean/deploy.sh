#!/bin/bash
# deploy.sh — Run on the droplet to pull and restart
# Usage: /home/vrenum/deploy.sh
set -e

echo "🚀 Deploying Vrenum..."

cd /home/vrenum/app

# Pull latest code
git pull origin main

# Activate venv and install any new deps
source .venv/bin/activate
pip install -r requirements.txt --quiet

# Run migrations
alembic upgrade head

# Restart app (graceful — supervisor handles zero-downtime)
sudo supervisorctl restart vrenum

echo "✅ Deploy complete"
curl -s http://127.0.0.1:8000/health
