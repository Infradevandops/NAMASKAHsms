#!/bin/bash
# Setup Environment Variables on VPS
# Run this BEFORE deploying

set -e

VPS_HOST="root@169.255.57.57"
APP_DIR="/var/www/vrenum"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         🔧 SETUP ENVIRONMENT VARIABLES 🔧                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if .env.production exists locally
if [ ! -f ".env.production" ]; then
    echo "❌ .env.production not found locally!"
    echo ""
    echo "Please create .env.production with your production credentials:"
    echo ""
    cat << 'EOF'
# Copy this template and fill in your values:

# Application
APP_NAME="VRENUM SMS"
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-secret-key-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
BASE_URL=https://vrenum.app

# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:password@host/database

# Redis (Upstash)
REDIS_URL=rediss://default:password@host:port

# TextVerified API
TEXTVERIFIED_API_KEY=your-api-key

# Paystack
PAYSTACK_SECRET_KEY=sk_live_xxx
PAYSTACK_PUBLIC_KEY=pk_live_xxx

# Email (Resend)
RESEND_API_KEY=re_xxx
RESEND_FROM_EMAIL=admin@vrenum.app

# Monitoring
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
MONITORING_ENABLED=true

# Google OAuth
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx
EOF
    exit 1
fi

echo "✓ Found .env.production locally"
echo ""
echo "📤 Uploading .env file to VPS..."

# Create app directory if it doesn't exist
ssh $VPS_HOST "mkdir -p $APP_DIR"

# Upload .env file
scp .env.production $VPS_HOST:$APP_DIR/.env

echo "✓ Environment file uploaded"
echo ""
echo "🔒 Setting secure permissions..."

ssh $VPS_HOST "chmod 600 $APP_DIR/.env"

echo "✓ Permissions set (600)"
echo ""
echo "✅ Environment setup complete!"
echo ""
echo "Next step: Run ./deploy_now.sh"
