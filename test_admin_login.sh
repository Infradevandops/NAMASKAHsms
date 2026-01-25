#!/bin/bash

# Test admin login credentials
# Usage: ./test_admin_login.sh [base_url]

BASE_URL=${1:-"http://127.0.0.1:8000"}
EMAIL="admin@namaskah.app"
PASSWORD="Namaskah@Admin2024"

echo "🔐 Testing admin login credentials..."
echo "URL: $BASE_URL"
echo "Email: $EMAIL"
echo ""

# Test login endpoint
echo "1️⃣ Testing login endpoint..."
RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

echo "Response: $RESPONSE"

# Check if login was successful
if echo "$RESPONSE" | grep -q "access_token"; then
    echo "✅ Login successful!"
    
    # Extract token
    TOKEN=$(echo "$RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo "Token: ${TOKEN:0:20}..."
    
    # Test authenticated endpoint
    echo ""
    echo "2️⃣ Testing authenticated endpoint..."
    USER_INFO=$(curl -s -X GET "$BASE_URL/api/auth/me" \
      -H "Authorization: Bearer $TOKEN")
    
    echo "User info: $USER_INFO"
    
    if echo "$USER_INFO" | grep -q "admin@namaskah.app"; then
        echo "✅ Authentication working!"
        
        # Test notifications endpoint
        echo ""
        echo "3️⃣ Testing notifications endpoint..."
        NOTIFICATIONS=$(curl -s -X GET "$BASE_URL/api/notifications" \
          -H "Authorization: Bearer $TOKEN")
        
        echo "Notifications: $NOTIFICATIONS"
        
        # Test verification history
        echo ""
        echo "4️⃣ Testing verification history..."
        HISTORY=$(curl -s -X GET "$BASE_URL/api/v1/verify/history" \
          -H "Authorization: Bearer $TOKEN")
        
        echo "History: $HISTORY"
        
    else
        echo "❌ Authentication failed"
    fi
    
else
    echo "❌ Login failed"
    echo "Response: $RESPONSE"
fi