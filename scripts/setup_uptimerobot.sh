#!/bin/bash
# UptimeRobot Monitoring Setup
# Addresses: Create UptimeRobot account, Add 3 monitors, Set up alerts

echo "🔍 UptimeRobot Monitoring Setup"
echo "================================"

# Configuration
BASE_URL="https://namaskah.onrender.com"
ALERT_EMAIL="admin@namaskah.app"

echo "📋 Required UptimeRobot Monitors:"
echo ""
echo "1. Main Site Monitor"
echo "   URL: $BASE_URL"
echo "   Type: HTTP(s)"
echo "   Keyword: 'Namaskah SMS'"
echo "   Interval: 5 minutes"
echo ""
echo "2. API Health Monitor" 
echo "   URL: $BASE_URL/health"
echo "   Type: HTTP(s)"
echo "   Expected: 200 status"
echo "   Interval: 5 minutes"
echo ""
echo "3. Authentication Monitor"
echo "   URL: $BASE_URL/api/auth/me"
echo "   Type: HTTP(s)"
echo "   Expected: 401 (unauthenticated)"
echo "   Interval: 10 minutes"
echo ""

echo "📧 Alert Configuration:"
echo "   Email: $ALERT_EMAIL"
echo "   SMS: Optional"
echo "   Webhook: Optional"
echo ""

echo "🚀 Setup Instructions:"
echo "1. Go to https://uptimerobot.com"
echo "2. Create free account"
echo "3. Add the 3 monitors above"
echo "4. Configure email alerts"
echo "5. Test each monitor"
echo ""

echo "✅ Verification Commands:"
echo "curl -I $BASE_URL"
echo "curl -I $BASE_URL/health"
echo "curl -I $BASE_URL/api/auth/me"