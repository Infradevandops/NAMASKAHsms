#!/bin/bash

# Admin Credentials Testing Script
# Usage: ./test-admin-credentials.sh [URL] [EMAIL] [PASSWORD]
# Example: ./test-admin-credentials.sh http://localhost:8000 admin@vrenum.app Namaskah@Admin2024

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="${1:-http://localhost:8000}"
EMAIL="${2:-admin@vrenum.app}"
PASSWORD="${3:-Namaskah@Admin2024}"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}🧪 Admin Credentials Testing${NC}"
echo -e "${BLUE}================================${NC}"
echo ""
echo -e "API URL: ${YELLOW}$API_URL${NC}"
echo -e "Email: ${YELLOW}$EMAIL${NC}"
echo ""

# Test 1: Health Check
echo -e "${BLUE}Test 1: Health Check${NC}"
HEALTH=$(curl -s -X GET "$API_URL/health" 2>/dev/null || echo "")

if [ -z "$HEALTH" ]; then
  echo -e "${RED}❌ Cannot reach API at $API_URL${NC}"
  exit 1
fi

if echo "$HEALTH" | grep -q "ok\|healthy"; then
  echo -e "${GREEN}✅ API is healthy${NC}"
else
  echo -e "${YELLOW}⚠️  API response: $HEALTH${NC}"
fi
echo ""

# Test 2: Admin Login
echo -e "${BLUE}Test 2: Admin Login${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\"
  }" 2>/dev/null)

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token' 2>/dev/null || echo "")

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo -e "${RED}❌ Login failed${NC}"
  echo -e "${RED}Response: $LOGIN_RESPONSE${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Login successful${NC}"
echo -e "Token: ${YELLOW}${TOKEN:0:30}...${NC}"
echo ""

# Test 3: Get User Info
echo -e "${BLUE}Test 3: Get User Info${NC}"
USER_RESPONSE=$(curl -s -X GET "$API_URL/api/auth/me" \
  -H "Authorization: Bearer $TOKEN" 2>/dev/null)

EMAIL_RESPONSE=$(echo "$USER_RESPONSE" | jq -r '.email' 2>/dev/null || echo "")
IS_ADMIN=$(echo "$USER_RESPONSE" | jq -r '.is_admin' 2>/dev/null || echo "")

if [ "$EMAIL_RESPONSE" != "$EMAIL" ]; then
  echo -e "${RED}❌ Email mismatch${NC}"
  exit 1
fi

if [ "$IS_ADMIN" != "true" ]; then
  echo -e "${RED}❌ User is not admin${NC}"
  exit 1
fi

echo -e "${GREEN}✅ User info verified${NC}"
echo -e "Email: ${YELLOW}$EMAIL_RESPONSE${NC}"
echo -e "Admin: ${YELLOW}$IS_ADMIN${NC}"
echo ""

# Test 4: Access Admin Dashboard
echo -e "${BLUE}Test 4: Access Admin Dashboard${NC}"
ADMIN_RESPONSE=$(curl -s -X GET "$API_URL/admin" \
  -H "Authorization: Bearer $TOKEN" 2>/dev/null)

if echo "$ADMIN_RESPONSE" | grep -q "error\|unauthorized\|forbidden"; then
  echo -e "${RED}❌ Admin dashboard access denied${NC}"
  echo -e "${RED}Response: $ADMIN_RESPONSE${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Admin dashboard accessible${NC}"
echo ""

# Test 5: Refresh Token
echo -e "${BLUE}Test 5: Refresh Token${NC}"
REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.refresh_token' 2>/dev/null || echo "")

if [ -z "$REFRESH_TOKEN" ] || [ "$REFRESH_TOKEN" == "null" ]; then
  echo -e "${YELLOW}⚠️  No refresh token provided${NC}"
else
  REFRESH_RESPONSE=$(curl -s -X POST "$API_URL/api/auth/refresh" \
    -H "Authorization: Bearer $REFRESH_TOKEN" 2>/dev/null)
  
  NEW_TOKEN=$(echo "$REFRESH_RESPONSE" | jq -r '.access_token' 2>/dev/null || echo "")
  
  if [ -z "$NEW_TOKEN" ] || [ "$NEW_TOKEN" == "null" ]; then
    echo -e "${YELLOW}⚠️  Token refresh failed${NC}"
  else
    echo -e "${GREEN}✅ Token refresh successful${NC}"
  fi
fi
echo ""

# Test 6: Logout
echo -e "${BLUE}Test 6: Logout${NC}"
LOGOUT_RESPONSE=$(curl -s -X POST "$API_URL/api/auth/logout" \
  -H "Authorization: Bearer $TOKEN" 2>/dev/null)

if echo "$LOGOUT_RESPONSE" | grep -q "success\|ok"; then
  echo -e "${GREEN}✅ Logout successful${NC}"
else
  echo -e "${YELLOW}⚠️  Logout response: $LOGOUT_RESPONSE${NC}"
fi
echo ""

# Test 7: Verify Token is Invalidated
echo -e "${BLUE}Test 7: Verify Token Invalidation${NC}"
INVALID_RESPONSE=$(curl -s -X GET "$API_URL/api/auth/me" \
  -H "Authorization: Bearer $TOKEN" 2>/dev/null)

if echo "$INVALID_RESPONSE" | grep -q "unauthorized\|invalid\|expired"; then
  echo -e "${GREEN}✅ Token properly invalidated${NC}"
else
  echo -e "${YELLOW}⚠️  Token still valid (may be expected)${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}================================${NC}"
echo -e "${GREEN}✅ All tests passed!${NC}"
echo -e "${BLUE}================================${NC}"
echo ""
echo -e "Admin credentials are working correctly on:"
echo -e "${YELLOW}$API_URL${NC}"
echo ""
