#!/bin/bash

# Test admin credentials against production
echo "🔐 Testing admin@namaskah.app credentials against production..."

PROD_URL="https://namaskah.app"
EMAIL="admin@namaskah.app"
PASSWORD="Namaskah@Admin2024"

echo "Testing login..."
RESPONSE=$(curl -s -X POST "$PROD_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

echo "Response: $RESPONSE"

if echo "$RESPONSE" | grep -q "access_token"; then
    echo "✅ Production login successful!"
    
    # Extract token
    TOKEN=$(echo "$RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo "Token: ${TOKEN:0:20}..."
    
    # Test notifications endpoint
    echo ""
    echo "Testing notifications..."
    NOTIFICATIONS=$(curl -s -X GET "$PROD_URL/api/notifications" \
      -H "Authorization: Bearer $TOKEN")
    
    echo "Notifications response: $NOTIFICATIONS"
    
    # Test verification history
    echo ""
    echo "Testing verification history..."
    HISTORY=$(curl -s -X GET "$PROD_URL/api/v1/verify/history" \
      -H "Authorization: Bearer $TOKEN")
    
    echo "History response: $HISTORY"
    
    # Save token for manual testing
    echo ""
    echo "🔧 For manual testing, use this token:"
    echo "localStorage.setItem('access_token', '$TOKEN');"
    
else
    echo "❌ Production login failed"
fi