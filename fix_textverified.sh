#!/bin/bash
# Fix TextVerified Library on VPS

set -e

SERVER="root@169.255.57.57"
APP_DIR="/root/NAMASKAHsms"

echo "🔧 Fixing TextVerified Integration..."
echo "====================================="

# Step 1: Check if library is installed
echo "📦 Step 1: Checking textverified library..."
ssh $SERVER << 'EOF'
cd /root/NAMASKAHsms
source .venv/bin/activate
python -c "import textverified; print('✅ textverified library installed')" 2>&1 || echo "❌ textverified library NOT installed"
EOF

# Step 2: Install if missing
echo ""
echo "📦 Step 2: Installing textverified library..."
ssh $SERVER << 'EOF'
cd /root/NAMASKAHsms
source .venv/bin/activate
pip install textverified --quiet
echo "✅ textverified library installed"
EOF

# Step 3: Verify credentials
echo ""
echo "🔑 Step 3: Verifying credentials..."
ssh $SERVER << 'EOF'
cd /root/NAMASKAHsms
echo "TEXTVERIFIED_API_KEY: $(grep TEXTVERIFIED_API_KEY .env | cut -d'=' -f2 | cut -c1-20)..."
echo "TEXTVERIFIED_EMAIL: $(grep TEXTVERIFIED_EMAIL .env | cut -d'=' -f2)"
EOF

# Step 4: Restart service
echo ""
echo "🔄 Step 4: Restarting service..."
ssh $SERVER "systemctl restart vrenum"
sleep 3

# Step 5: Check logs
echo ""
echo "✅ Step 5: Checking logs..."
ssh $SERVER "journalctl -u vrenum -n 30 --no-pager | grep -i textverified || echo 'No TextVerified messages in logs'"

echo ""
echo "====================================="
echo "✅ Fix complete!"
echo ""
echo "Watch logs to verify:"
echo "  ./logs_audit.sh live"
