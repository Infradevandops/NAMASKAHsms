#!/bin/bash
# Verify TextVerified is working

echo "🔍 Verifying TextVerified Status..."
echo "===================================="

ssh root@169.255.57.57 << 'EOF'
echo "📋 Last 30 log lines:"
journalctl -u vrenum -n 30 --no-pager | tail -20

echo ""
echo "===================================="
echo "🔎 Searching for TextVerified messages:"
journalctl -u vrenum --since "2 minutes ago" --no-pager | grep -i textverified || echo "No TextVerified messages in last 2 minutes"

echo ""
echo "===================================="
echo "✅ Service Status:"
systemctl is-active vrenum && echo "Service is RUNNING" || echo "Service is NOT running"
EOF

echo ""
echo "===================================="
echo "✅ Verification complete!"
echo ""
echo "Look for:"
echo "  ✅ 'TextVerified client initialized successfully'"
echo "  ❌ 'TextVerified service disabled'"
