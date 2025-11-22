#!/bin/bash

echo "🔍 NAMASKAH SYSTEM STATUS CHECK"
echo "================================"

# Check server process
echo "📡 SERVER STATUS:"
if ps aux | grep -v grep | grep uvicorn > /dev/null; then
    echo "✅ Server running on PID: $(ps aux | grep -v grep | grep uvicorn | awk '{print $2}')"
else
    echo "❌ Server not running"
fi

# Check port availability
echo ""
echo "🔌 PORT STATUS:"
for port in 8000 8001 8002; do
    if lsof -i:$port > /dev/null 2>&1; then
        echo "✅ Port $port: BUSY"
    else
        echo "⚪ Port $port: FREE"
    fi
done

# Test API endpoints
echo ""
echo "🌐 API ENDPOINTS:"
BASE_URL="http://localhost:8001"

# Test homepage
if curl -s -o /dev/null -w "%{http_code}" $BASE_URL/ | grep -q "200"; then
    echo "✅ Homepage: $BASE_URL/"
else
    echo "❌ Homepage: $BASE_URL/"
fi

# Test login page
if curl -s -o /dev/null -w "%{http_code}" $BASE_URL/auth/login | grep -q "200"; then
    echo "✅ Login: $BASE_URL/auth/login"
else
    echo "❌ Login: $BASE_URL/auth/login"
fi

# Test dashboard
if curl -s -o /dev/null -w "%{http_code}" $BASE_URL/app | grep -q "200"; then
    echo "✅ Dashboard: $BASE_URL/app"
else
    echo "❌ Dashboard: $BASE_URL/app"
fi

# Test login API
if curl -s -X POST $BASE_URL/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@namaskah.app","password":"admin123"}' | grep -q "success"; then
    echo "✅ Login API: $BASE_URL/api/auth/login"
else
    echo "❌ Login API: $BASE_URL/api/auth/login"
fi

# Test countries API
if curl -s $BASE_URL/api/countries/ | grep -q "success"; then
    echo "✅ Countries API: $BASE_URL/api/countries/"
else
    echo "❌ Countries API: $BASE_URL/api/countries/"
fi

# Database check
echo ""
echo "🗄️ DATABASE STATUS:"
if [ -f "namaskah_dev.db" ]; then
    echo "✅ Database file exists"
    echo "📊 Database size: $(ls -lh namaskah_dev.db | awk '{print $5}')"
else
    echo "❌ Database file missing"
fi

echo ""
echo "🎯 QUICK ACCESS URLS:"
echo "   Homepage: $BASE_URL/"
echo "   Login: $BASE_URL/auth/login"
echo "   Dashboard: $BASE_URL/app"
echo ""
echo "🔑 LOGIN CREDENTIALS:"
echo "   Email: admin@namaskah.app"
echo "   Password: admin123"