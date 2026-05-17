#!/bin/bash
# Quick Deploy Script for Refund System Fix v4.7.2
# Run on production server: bash deploy_refund_fix.sh

set -e

echo "🚀 Deploying Refund System Fix v4.7.2"
echo "======================================"
echo ""

# Check if running on production server
if [ ! -d "/root/NAMASKAHsms" ]; then
    echo "❌ Error: Not on production server"
    echo "This script must be run on vm518ftop.vrenum.app.com"
    exit 1
fi

cd /root/NAMASKAHsms

# Backup current file
BACKUP_FILE="app/services/auto_refund_service.py.backup.$(date +%Y%m%d_%H%M%S)"
echo "📦 Creating backup: $BACKUP_FILE"
cp app/services/auto_refund_service.py "$BACKUP_FILE"

# Pull latest code from repo
echo ""
echo "📥 Pulling latest code..."
git pull origin main || {
    echo "⚠️  Git pull failed. Applying manual fixes..."

    # Manual fix if git pull fails
    echo "Applying Fix #1: Add 'error' to refundable statuses..."
    sed -i '58s/if verification.status not in \["timeout", "cancelled", "failed"\]:/if verification.status not in ["timeout", "cancelled", "failed", "error"]:/' app/services/auto_refund_service.py

    echo "Applying Fix #2: Fix Decimal/float type mismatch..."
    sed -i '73s/(user.credits or 0.0) + refund_amount/(float(user.credits) if user.credits else 0.0) + float(refund_amount)/' app/services/auto_refund_service.py
}

# Verify fixes applied
echo ""
echo "✅ Verifying fixes..."
echo "Line 58 (status check):"
sed -n '58p' app/services/auto_refund_service.py | grep -q "error" && echo "  ✓ 'error' status added" || echo "  ✗ Fix not applied"

echo "Line 73 (type conversion):"
sed -n '73p' app/services/auto_refund_service.py | grep -q "float(user.credits)" && echo "  ✓ Type conversion added" || echo "  ✗ Fix not applied"

# Restart service
echo ""
echo "🔄 Restarting Vrenum service..."
systemctl restart vrenum

# Wait for service to start
sleep 5

# Check service status
if systemctl is-active --quiet vrenum; then
    echo "✅ Service restarted successfully"
else
    echo "❌ Service failed to start!"
    echo "Rolling back..."
    cp "$BACKUP_FILE" app/services/auto_refund_service.py
    systemctl restart vrenum
    exit 1
fi

# Monitor logs for 10 seconds
echo ""
echo "📊 Monitoring logs (10 seconds)..."
timeout 10 tail -f logs/app.log | grep -i "refund\|error" || true

echo ""
echo "======================================"
echo "✅ Deployment Complete!"
echo ""
echo "Next steps:"
echo "1. Monitor logs: tail -f logs/app.log | grep -i refund"
echo "2. Check refunds in 5 minutes (enforcer cycle)"
echo "3. Verify user credits increased"
echo ""
echo "Rollback command (if needed):"
echo "  cp $BACKUP_FILE app/services/auto_refund_service.py"
echo "  systemctl restart vrenum"
echo ""
