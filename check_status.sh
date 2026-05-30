#!/bin/bash
# Comprehensive TextVerified verification

echo "🔍 Comprehensive TextVerified Status Check"
echo "=========================================="

ssh root@169.255.57.57 << 'EOF'
echo "1️⃣ Service Status:"
systemctl is-active vrenum && echo "   ✅ Service is RUNNING" || echo "   ❌ Service is NOT running"

echo ""
echo "2️⃣ Last 40 log lines:"
journalctl -u vrenum -n 40 --no-pager | tail -30

echo ""
echo "3️⃣ Searching for TextVerified in recent logs:"
journalctl -u vrenum --since "2 minutes ago" --no-pager | grep -i "textverified\|startup complete" || echo "   No TextVerified messages found"

echo ""
echo "4️⃣ Environment variables in service:"
systemctl show vrenum --property=Environment | head -1

echo ""
echo "5️⃣ Check if .env is being loaded:"
grep -c "EnvironmentFile" /etc/systemd/system/vrenum.service && echo "   ✅ EnvironmentFile directive present" || echo "   ❌ EnvironmentFile directive missing"
EOF

echo ""
echo "=========================================="
echo "Analysis complete!"
