#!/bin/bash
# Fix DATABASE_URL SSL Mode on VPS

set -e

VPS_HOST="root@169.255.57.57"
APP_DIR="/var/www/vrenum"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         🔧 FIX DATABASE SSL CONNECTION 🔧                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "📝 Fixing DATABASE_URL to include SSL mode..."

ssh $VPS_HOST bash << 'ENDSSH'
cd /var/www/vrenum

# Backup current .env
cp .env .env.backup

# Fix DATABASE_URL - add ?sslmode=require if not present
if grep -q "DATABASE_URL.*sslmode" .env; then
    echo "✓ DATABASE_URL already has sslmode parameter"
else
    echo "Adding sslmode=require to DATABASE_URL..."
    sed -i 's|DATABASE_URL=postgresql://\([^?]*\)$|DATABASE_URL=postgresql://\1?sslmode=require|' .env
    echo "✓ DATABASE_URL updated"
fi

echo ""
echo "Current DATABASE_URL (masked):"
grep "DATABASE_URL" .env | sed 's/:[^@]*@/:***@/'

ENDSSH

echo ""
echo "✅ Database URL fixed!"
echo ""
echo "Next step: Run ./deploy_now.sh again"
