#!/bin/bash
# One-command TextVerified fix

echo "🔧 Fixing TextVerified configuration..."
echo ""

ssh root@169.255.57.57 "cd /root/NAMASKAHsms && grep -q 'TEXTVERIFIED_USERNAME' .env || echo 'TEXTVERIFIED_USERNAME=huff_06psalm@icloud.com' >> .env && echo '✅ Added TEXTVERIFIED_USERNAME' && systemctl restart vrenum && echo '🔄 Service restarted' && sleep 3 && echo '' && echo '📊 Checking logs...' && journalctl -u vrenum -n 20 --no-pager | grep -i textverified"

echo ""
echo "✅ Done! Check above for 'TextVerified client initialized successfully'"
