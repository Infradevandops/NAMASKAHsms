#!/bin/bash
# Fix duplicate TEXTVERIFIED_USERNAME

echo "🔧 Fixing duplicate TEXTVERIFIED_USERNAME..."
echo ""

ssh root@169.255.57.57 << 'EOF'
cd /root/NAMASKAHsms

# Backup .env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Remove duplicate TEXTVERIFIED_USERNAME lines, keep only one
grep -v "TEXTVERIFIED_USERNAME" .env > .env.tmp
echo "TEXTVERIFIED_USERNAME=huff_06psalm@icloud.com" >> .env.tmp
mv .env.tmp .env

echo "✅ Fixed .env file"
echo ""
echo "📋 Current TEXTVERIFIED variables:"
grep TEXTVERIFIED .env | sort

echo ""
echo "🔄 Restarting service..."
systemctl restart vrenum

sleep 3

echo ""
echo "📊 Checking logs..."
journalctl -u vrenum -n 20 --no-pager | grep -i textverified
EOF

echo ""
echo "✅ Done! Check above for 'TextVerified client initialized successfully'"
