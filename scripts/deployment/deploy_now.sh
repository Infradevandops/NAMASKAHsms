#!/bin/bash
# Quick Deploy to VPS: 169.255.57.57 (vm518ftop.vrenum.app)
# Version: 4.7.3
# Date: May 22, 2026

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
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║         🚀 VRENUM SMS - PRODUCTION DEPLOYMENT 🚀          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
info "VPS: $VPS_HOST"
info "Repository: $REPO_URL"
info "Branch: $BRANCH"
echo ""

# Check SSH connection
log "Testing SSH connection..."
if ! ssh -o ConnectTimeout=5 $VPS_HOST "echo 'SSH connection successful'" &>/dev/null; then
    error "Cannot connect to VPS. Please check SSH access."
fi
log "✓ SSH connection verified"

# Confirm deployment
echo ""
warn "This will deploy to PRODUCTION server: $VPS_HOST"
read -p "Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    error "Deployment cancelled by user"
fi

log "🚀 Starting deployment..."

# Deploy to VPS
ssh $VPS_HOST bash << 'ENDSSH'
set -e

APP_DIR="/var/www/vrenum"
REPO_URL="https://github.com/Infradevandops/NAMASKAHsms.git"
BRANCH="main"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Step 1: Pulling latest code from GitHub..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if app directory exists
if [ ! -d "$APP_DIR" ]; then
    echo "Creating app directory..."
    mkdir -p $APP_DIR
    cd $APP_DIR
    git clone $REPO_URL .
else
    cd $APP_DIR

    # Backup current version
    echo "💾 Creating backup..."
    BACKUP_DIR="${APP_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
    cp -r $APP_DIR $BACKUP_DIR
    echo "✓ Backup created: $BACKUP_DIR"

    # Pull latest changes
    echo "Fetching latest changes..."
    git fetch origin
    git reset --hard origin/$BRANCH
    git pull origin $BRANCH
fi

echo "✓ Code updated to latest version"
git log --oneline -1

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Step 2: Installing dependencies..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Setup virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "✓ Dependencies installed"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🗄️  Step 3: Running database migrations..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

alembic upgrade head

echo "✓ Database migrations completed"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 Step 4: Restarting application..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create logs directory if it doesn't exist
mkdir -p logs

# Restart based on process manager
if command -v systemctl &> /dev/null && systemctl is-active --quiet vrenum; then
    echo "Restarting via systemd..."
    sudo systemctl restart vrenum
    sleep 3
    sudo systemctl status vrenum --no-pager
elif command -v supervisorctl &> /dev/null; then
    echo "Restarting via supervisor..."
    sudo supervisorctl restart vrenum
else
    echo "Restarting via gunicorn..."
    pkill -f "gunicorn.*main:app" || true
    sleep 2
    nohup gunicorn main:app \
        --workers 2 \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:8000 \
        --daemon \
        --pid gunicorn.pid \
        --access-logfile logs/access.log \
        --error-logfile logs/error.log
fi

echo "✓ Application restarted"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🏥 Step 5: Health check..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "⏳ Waiting for application to start..."
sleep 5

# Health check
if curl -f http://localhost:8000/health &>/dev/null; then
    echo "✅ Health check PASSED"
    curl -s http://localhost:8000/health | python3 -m json.tool || echo "Health endpoint responded"
else
    echo "❌ Health check FAILED"
    echo "Checking logs..."
    tail -20 logs/error.log
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ DEPLOYMENT SUCCESSFUL!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ENDSSH

log "✅ Deployment completed successfully!"
echo ""
info "🌐 Application URL: https://vrenum.app"
info "🔧 Admin Panel: https://vrenum.app/admin"
info "📊 API Docs: https://vrenum.app/docs"
info "🏥 Health Check: https://vrenum.app/health"
echo ""
log "📊 Monitoring:"
info "   Sentry: https://dev-vp.sentry.io/issues/"
info "   Better Stack: https://uptime.betterstack.com/team/t545038/monitors/4422808"
echo ""
warn "⚠️  Monitor the application for the next 24 hours"
warn "⚠️  Check Sentry for any errors"
warn "⚠️  Verify all features are working"
echo ""
log "🎉 Deployment complete! Happy launching! 🚀"
