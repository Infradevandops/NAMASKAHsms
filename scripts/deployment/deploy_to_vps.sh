#!/bin/bash
# Deploy to VPS: root@vm518ftop.vrenum.app.com
set -e

# Configuration
VPS_HOST="root@169.255.57.57"
APP_DIR="/var/www/vrenum"
REPO_URL="https://github.com/Infradevandops/NAMASKAHsms.git"
BRANCH="main"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

log "🚀 Deploying to VPS: $VPS_HOST"

# Deploy script to run on VPS
ssh $VPS_HOST bash << 'ENDSSH'
set -e

APP_DIR="/var/www/vrenum"
REPO_URL="https://github.com/Infradevandops/NAMASKAHsms.git"
BRANCH="main"

echo "📦 Pulling latest code from GitHub..."
cd $APP_DIR || exit 1

# Backup current version
echo "💾 Creating backup..."
cp -r $APP_DIR ${APP_DIR}_backup_$(date +%Y%m%d_%H%M%S)

# Pull latest changes
git fetch origin
git reset --hard origin/$BRANCH
git pull origin $BRANCH

echo "📋 Installing dependencies..."
source venv/bin/activate || python3 -m venv venv && source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "🗄️ Running database migrations..."
alembic upgrade head

echo "🔄 Restarting application..."
# Restart based on your process manager
if command -v systemctl &> /dev/null; then
    sudo systemctl restart vrenum
elif command -v supervisorctl &> /dev/null; then
    sudo supervisorctl restart vrenum
elif [ -f gunicorn.pid ]; then
    kill -HUP $(cat gunicorn.pid)
else
    pkill -f "gunicorn.*main:app" || true
    nohup gunicorn main:app \
        --workers 2 \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:8000 \
        --daemon \
        --pid gunicorn.pid \
        --access-logfile logs/access.log \
        --error-logfile logs/error.log
fi

echo "⏳ Waiting for application to start..."
sleep 5

echo "🏥 Health check..."
if curl -f http://localhost:8000/health &>/dev/null; then
    echo "✅ Deployment successful!"
else
    echo "❌ Health check failed!"
    exit 1
fi

ENDSSH

log "✅ Deployment completed successfully!"
log "🌐 Check: https://vrenum.app"
