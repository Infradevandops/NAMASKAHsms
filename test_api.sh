#!/bin/bash

# Test Real API Integration

echo "🧪 Testing Namaskah SMS Real API Integration"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base URL
BASE_URL="http://localhost:8000"

# Test 1: Health Check
echo -e "${YELLOW}Test 1: Health Check${NC}"
curl -s -X GET "$BASE_URL/api/system/health" | python3 -m json.tool
echo ""

# Test 2: Login
echo -e "${YELLOW}Test 2: Login${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@namaskah.app",
    "password": "admin123"
  }')

echo "$LOGIN_RESPONSE" | python3 -m json.tool

# Extract token
TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Failed to get token${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Token obtained${NC}"
echo ""

# Test 3: Get Balance
echo -e "${YELLOW}Test 3: Get Account Balance${NC}"
curl -s -X GET "$BASE_URL/api/verify/balance" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | python3 -m json.tool
echo ""

# Test 4: Get Services
echo -e "${YELLOW}Test 4: Get Available Services${NC}"
curl -s -X GET "$BASE_URL/api/verify/services" \
  -H "Content-Type: application/json" | python3 -m json.tool | head -30
echo ""

# Test 5: Get Area Codes
echo -e "${YELLOW}Test 5: Get Area Codes${NC}"
curl -s -X GET "$BASE_URL/api/verify/area-codes" \
  -H "Content-Type: application/json" | python3 -m json.tool | head -30
echo ""

# Test 6: Create Verification
echo -e "${YELLOW}Test 6: Create Real Verification${NC}"
VERIFY_RESPONSE=$(curl -s -X POST "$BASE_URL/api/verify/create" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service": "telegram",
    "area_code": "415"
  }')

echo "$VERIFY_RESPONSE" | python3 -m json.tool

# Extract verification ID
VERIFY_ID=$(echo "$VERIFY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)

if [ -z "$VERIFY_ID" ]; then
    echo -e "${RED}❌ Failed to create verification${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Verification created: $VERIFY_ID${NC}"
echo ""

# Test 7: Check Verification Status
echo -e "${YELLOW}Test 7: Check Verification Status${NC}"
curl -s -X GET "$BASE_URL/api/verify/$VERIFY_ID/status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | python3 -m json.tool
echo ""

# Test 8: Create Rental
echo -e "${YELLOW}Test 8: Create Real Rental${NC}"
RENTAL_RESPONSE=$(curl -s -X POST "$BASE_URL/api/rentals/create" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service": "telegram",
    "duration_days": 30,
    "renewable": true
  }')

echo "$RENTAL_RESPONSE" | python3 -m json.tool

# Extract rental ID
RENTAL_ID=$(echo "$RENTAL_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)

if [ -z "$RENTAL_ID" ]; then
    echo -e "${RED}❌ Failed to create rental${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Rental created: $RENTAL_ID${NC}"
echo ""

# Test 9: Get Active Rentals
echo -e "${YELLOW}Test 9: Get Active Rentals${NC}"
curl -s -X GET "$BASE_URL/api/rentals/active" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | python3 -m json.tool
echo ""

# Test 10: Get Rental Details
echo -e "${YELLOW}Test 10: Get Rental Details${NC}"
curl -s -X GET "$BASE_URL/api/rentals/$RENTAL_ID/details" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | python3 -m json.tool
echo ""

echo -e "${GREEN}✅ All tests completed!${NC}"
