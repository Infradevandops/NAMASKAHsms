#!/bin/bash
# Deploy Balance Fix to Production

set -e

SERVER="root@169.255.57.57"
APP_DIR="/root/NAMASKAHsms"

echo "🚨 CRITICAL FIX: Deploying Admin Balance Correction"
echo "===================================================="
echo ""
echo "Issue: Admin dashboard shows \$12.10 (platform credits)"
echo "Fix: Admin will now see \$2.40 (TextVerified balance)"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# Step 1: Commit changes
echo ""
echo "📝 Step 1: Committing changes..."
git add app/api/billing/credit_endpoints.py BALANCE_ISSUE_ANALYSIS.md
git commit -m "fix: Admin balance now shows TextVerified API balance instead of platform credits

CRITICAL FIX:
- Admin users now see TextVerified account balance (\$2.40)
- Regular users still see their platform credits
- Prevents confusion when admin balance != provider balance
- Adds platform_credits field for admin to see both balances

Closes: Balance mismatch issue"

echo "✅ Changes committed"

# Step 2: Push to GitHub
echo ""
echo "📤 Step 2: Pushing to GitHub..."
git push origin main
echo "✅ Pushed to GitHub"

# Step 3: Deploy to VPS
echo ""
echo "🚀 Step 3: Deploying to VPS..."
ssh $SERVER << 'EOF'
cd /root/NAMASKAHsms

# Pull latest code
git pull origin main

# Restart service
systemctl restart vrenum

echo "✅ Service restarted"

# Wait for startup
sleep 5

# Check if service is running
systemctl is-active vrenum && echo "✅ Service is running" || echo "❌ Service failed to start"
EOF

# Step 4: Verify fix
echo ""
echo "🔍 Step 4: Verifying fix..."
echo ""
echo "Checking logs for balance initialization..."
ssh $SERVER "journalctl -u vrenum --since '30 seconds ago' --no-pager | grep -i 'balance\|textverified' | tail -10"

echo ""
echo "===================================================="
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Login to admin dashboard: https://vrenum.app/admin"
echo "2. Check balance display - should show \$2.40"
echo "3. Verify 'platform_credits' shows \$12.10 in API response"
echo ""
echo "Test API directly:"
echo "  curl -H 'Authorization: Bearer <admin_token>' https://vrenum.app/api/billing/balance"
echo ""
