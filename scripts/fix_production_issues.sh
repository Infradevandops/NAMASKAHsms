#!/bin/bash
# Production Issue Fix Script
# Run this on your server: vm518ftop.vrenum.app.com

set -e

echo "🔧 Namaskah Production Fix Script"
echo "=================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (sudo)"
    exit 1
fi

cd /root/NAMASKAHsms

# 1. Check TextVerified credentials
echo "1️⃣ Checking TextVerified configuration..."
if grep -q "TEXTVERIFIED_API_KEY=" .env && ! grep -q "TEXTVERIFIED_API_KEY=$" .env; then
    echo "✅ TextVerified API key found"
else
    echo "❌ TextVerified API key missing or empty"
    echo ""
    echo "Please add to .env:"
    echo "TEXTVERIFIED_API_KEY=your_actual_key"
    echo "TEXTVERIFIED_ENABLED=true"
    echo ""
    read -p "Enter your TextVerified API key: " api_key
    if [ ! -z "$api_key" ]; then
        echo "TEXTVERIFIED_API_KEY=$api_key" >> .env
        echo "TEXTVERIFIED_ENABLED=true" >> .env
        echo "✅ Added TextVerified credentials"
    fi
fi

# 2. Fix async snapshot error
echo ""
echo "2️⃣ Checking for async context manager issues..."
if grep -q "__aenter__" logs/app.log; then
    echo "⚠️  Found async context manager error in logs"
    echo "This will be fixed in the code..."
fi

# 3. Restart service
echo ""
echo "3️⃣ Restarting Namaskah service..."
systemctl restart namaskah
sleep 3

# 4. Check service status
echo ""
echo "4️⃣ Checking service status..."
if systemctl is-active --quiet namaskah; then
    echo "✅ Service is running"
else
    echo "❌ Service failed to start"
    echo "Logs:"
    journalctl -u namaskah -n 20 --no-pager
    exit 1
fi

# 5. Test health endpoint
echo ""
echo "5️⃣ Testing health endpoint..."
response=$(curl -s http://localhost:8000/health)
if echo "$response" | grep -q "healthy"; then
    echo "✅ Health check passed: $response"
else
    echo "❌ Health check failed: $response"
fi

# 6. Check recent logs
echo ""
echo "6️⃣ Recent application logs:"
echo "----------------------------"
tail -n 10 logs/app.log

echo ""
echo "=================================="
echo "✅ Fix script completed!"
echo ""
echo "Next steps:"
echo "1. Visit https://vrenum.app/dashboard"
echo "2. Try creating a new SMS verification"
echo "3. Monitor logs: tail -f logs/app.log"
echo ""
