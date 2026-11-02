#!/bin/bash
set -e

SERVER="root@<your-vps-ip>"
REMOTE_DIR="~/vrenum"
LOCAL_DIR="/Users/machine/My Drive/Github Projects/Vrenum"

echo "🔄 Syncing files to server..."
rsync -avz \
  --exclude='.venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.git' \
  --exclude='htmlcov' \
  --exclude='logs' \
  --exclude='uploads' \
  "$LOCAL_DIR/" "$SERVER:$REMOTE_DIR/"

echo "🐳 Building and restarting containers..."
ssh "$SERVER" "cd $REMOTE_DIR && docker compose build --no-cache && docker compose up -d"

echo "⏳ Waiting for app to be healthy..."
sleep 20

echo "✅ Health check..."
curl -s https://vrenum.app/health
echo ""
echo "🎉 Deploy complete!"
