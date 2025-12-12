#!/bin/bash

# 🧪 Namaskah SMS API Testing Script
# Purpose: Automated testing of all API services
# Version: 2.5.0
# Date: December 5, 2025

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
TEST_EMAIL="test_$(date +%s)@example.com"
TEST_PASSWORD="TestPassword123!"
VERBOSE="${VERBOSE:-false}"

# Global variables
ACCESS_TOKEN=""
REFRESH_TOKEN=""
USER_ID=""
VERIFICATION_ID=""

# Helper functions
print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

print_test() {
    echo -e "${BLUE}→ Testing: $1${NC}"
}

# Check if server is running
check_server() {
    print_header "Checking Server Status"
    
    if curl -s "$BASE_URL/api/system/health" > /dev/null 2>&1; then
        print_success "Server is running at $BASE_URL"
    else
        print_error "Server is not running at $BASE_URL"
        echo "Start the server with: ./start.sh"
        exit 1
    fi
}

# Test 1: Health Check
test_health_check() {
    print_header "Test 1: Health Check"
    print_test "GET /api/system/health"
    
    response=$(curl -s "$BASE_URL/api/system/health")
    
    if echo "$response" | grep -q "healthy"; then
        print_success "Health check passed"
        [ "$VERBOSE" = "true" ] && echo "Response: $response"
    else
        print_error "Health check failed"
        echo "Response: $response"
        return 1
    fi
}

# Test 2: List Countries
test_list_countries() {
    print_header "Test 2: List Countries"
    print_test "GET /api/countries/"
    
    response=$(curl -s "$BASE_URL/api/countries/")
    
    if echo "$response" | grep -q "countries\|US\|RU"; then
        print_success "Countries list retrieved"
        [ "$VERBOSE" = "true" ] && echo "Response: $response" | head -20
    else
        print_error "Failed to retrieve countries"
        echo "Response: $response"
        return 1
    fi
}

# Test 3: User Registration
test_user_registration() {
    print_header "Test 3: User Registration"
    print_test "POST /api/auth/register"
    
    response=$(curl -s -X POST "$BASE_URL/api/auth/register" \
        -H "Content-Type: application/json" \
        -d "{
            \"email\": \"$TEST_EMAIL\",
            \"password\": \"$TEST_PASSWORD\"
        }")
    
    if echo "$response" | grep -q "access_token"; then
        ACCESS_TOKEN=$(echo "$response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
        REFRESH_TOKEN=$(echo "$response" | grep -o '"refresh_token":"[^"]*' | cut -d'"' -f4)
        USER_ID=$(echo "$response" | grep -o '"id":"[^"]*' | cut -d'"' -f4 | head -1)
        
        print_success "User registered successfully"
        print_info "Email: $TEST_EMAIL"
        print_info "User ID: $USER_ID"
        [ "$VERBOSE" = "true" ] && echo "Response: $response" | head -20
    else
        print_error "User registration failed"
        echo "Response: $response"
        return 1
    fi
}

# Test 4: Get User Profile
test_get_profile() {
    print_header "Test 4: Get User Profile"
    print_test "GET /api/user/profile"
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "No access token available"
        return 1
    fi
    
    response=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
        "$BASE_URL/api/user/profile")
    
    if echo "$response" | grep -q "email"; then
        print_success "User profile retrieved"
        [ "$VERBOSE" = "true" ] && echo "Response: $response" | head -20
    else
        print_error "Failed to retrieve user profile"
        echo "Response: $response"
        return 1
    fi
}

# Test 5: Get User Balance
test_get_balance() {
    print_header "Test 5: Get User Balance"
    print_test "GET /api/user/balance"
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "No access token available"
        return 1
    fi
    
    response=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
        "$BASE_URL/api/user/balance")
    
    if echo "$response" | grep -q "credits"; then
        print_success "User balance retrieved"
        [ "$VERBOSE" = "true" ] && echo "Response: $response"
    else
        print_error "Failed to retrieve user balance"
        echo "Response: $response"
        return 1
    fi
}

# Test 6: Get Services for Country
test_get_services() {
    print_header "Test 6: Get Services for Country"
    print_test "GET /api/countries/US/services"
    
    response=$(curl -s "$BASE_URL/api/countries/US/services")
    
    if echo "$response" | grep -q "services\|telegram\|whatsapp"; then
        print_success "Services retrieved for US"
        [ "$VERBOSE" = "true" ] && echo "Response: $response" | head -20
    else
        print_error "Failed to retrieve services"
        echo "Response: $response"
        return 1
    fi
}

# Test 7: Add Credits
test_add_credits() {
    print_header "Test 7: Add Credits"
    print_test "POST /api/billing/add-credits"
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "No access token available"
        return 1
    fi
    
    response=$(curl -s -X POST "$BASE_URL/api/billing/add-credits" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"amount": 10}')
    
    if echo "$response" | grep -q "success\|amount_added"; then
        print_success "Credits added successfully"
        [ "$VERBOSE" = "true" ] && echo "Response: $response"
    else
        print_error "Failed to add credits"
        echo "Response: $response"
        return 1
    fi
}

# Test 8: Create Verification
test_create_verification() {
    print_header "Test 8: Create Verification"
    print_test "POST /api/verify/create"
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "No access token available"
        return 1
    fi
    
    response=$(curl -s -X POST "$BASE_URL/api/verify/create" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "service_name": "telegram",
            "country": "US",
            "pricing_tier": "standard"
        }')
    
    if echo "$response" | grep -q "id\|phone_number"; then
        VERIFICATION_ID=$(echo "$response" | grep -o '"id":"[^"]*' | cut -d'"' -f4 | head -1)
        print_success "Verification created successfully"
        print_info "Verification ID: $VERIFICATION_ID"
        [ "$VERBOSE" = "true" ] && echo "Response: $response"
    else
        print_error "Failed to create verification"
        echo "Response: $response"
        return 1
    fi
}

# Test 9: Check Verification Status
test_check_verification_status() {
    print_header "Test 9: Check Verification Status"
    print_test "GET /api/verify/{id}"
    
    if [ -z "$ACCESS_TOKEN" ] || [ -z "$VERIFICATION_ID" ]; then
        print_error "No access token or verification ID available"
        return 1
    fi
    
    response=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
        "$BASE_URL/api/verify/$VERIFICATION_ID")
    
    if echo "$response" | grep -q "status\|phone_number"; then
        print_success "Verification status retrieved"
        [ "$VERBOSE" = "true" ] && echo "Response: $response"
    else
        print_error "Failed to retrieve verification status"
        echo "Response: $response"
        return 1
    fi
}

# Test 10: Get SMS Inbox
test_get_sms_inbox() {
    print_header "Test 10: Get SMS Inbox"
    print_test "GET /api/sms/inbox"
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "No access token available"
        return 1
    fi
    
    response=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
        "$BASE_URL/api/sms/inbox")
    
    if echo "$response" | grep -q "messages"; then
        print_success "SMS inbox retrieved"
        [ "$VERBOSE" = "true" ] && echo "Response: $response"
    else
        print_error "Failed to retrieve SMS inbox"
        echo "Response: $response"
        return 1
    fi
}

# Test 11: Get Analytics Dashboard
test_get_analytics() {
    print_header "Test 11: Get Analytics Dashboard"
    print_test "GET /api/analytics/dashboard"
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "No access token available"
        return 1
    fi
    
    response=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
        "$BASE_URL/api/analytics/dashboard")
    
    if echo "$response" | grep -q "total_verifications\|success_rate"; then
        print_success "Analytics dashboard retrieved"
        [ "$VERBOSE" = "true" ] && echo "Response: $response"
    else
        print_error "Failed to retrieve analytics"
        echo "Response: $response"
        return 1
    fi
}

# Test 12: Get Payment History
test_get_payment_history() {
    print_header "Test 12: Get Payment History"
    print_test "GET /api/billing/history"
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "No access token available"
        return 1
    fi
    
    response=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
        "$BASE_URL/api/billing/history")
    
    if echo "$response" | grep -q "payments"; then
        print_success "Payment history retrieved"
        [ "$VERBOSE" = "true" ] && echo "Response: $response"
    else
        print_error "Failed to retrieve payment history"
        echo "Response: $response"
        return 1
    fi
}

# Test 13: Refresh Token
test_refresh_token() {
    print_header "Test 13: Refresh Token"
    print_test "POST /api/auth/refresh"
    
    if [ -z "$REFRESH_TOKEN" ]; then
        print_error "No refresh token available"
        return 1
    fi
    
    response=$(curl -s -X POST "$BASE_URL/api/auth/refresh" \
        -H "Authorization: Bearer $REFRESH_TOKEN")
    
    if echo "$response" | grep -q "access_token"; then
        NEW_ACCESS_TOKEN=$(echo "$response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
        ACCESS_TOKEN="$NEW_ACCESS_TOKEN"
        print_success "Token refreshed successfully"
        [ "$VERBOSE" = "true" ] && echo "Response: $response" | head -10
    else
        print_error "Failed to refresh token"
        echo "Response: $response"
        return 1
    fi
}

# Test 14: Update User Profile
test_update_profile() {
    print_header "Test 14: Update User Profile"
    print_test "PUT /api/user/profile"
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "No access token available"
        return 1
    fi
    
    response=$(curl -s -X PUT "$BASE_URL/api/user/profile" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Test User",
            "phone": "+1234567890",
            "country": "US"
        }')
    
    if echo "$response" | grep -q "success"; then
        print_success "User profile updated successfully"
        [ "$VERBOSE" = "true" ] && echo "Response: $response"
    else
        print_error "Failed to update user profile"
        echo "Response: $response"
        return 1
    fi
}

# Test 15: Logout
test_logout() {
    print_header "Test 15: Logout"
    print_test "POST /api/auth/logout"
    
    if [ -z "$ACCESS_TOKEN" ]; then
        print_error "No access token available"
        return 1
    fi
    
    response=$(curl -s -X POST "$BASE_URL/api/auth/logout" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    
    if echo "$response" | grep -q "success\|Logged out"; then
        print_success "User logged out successfully"
        [ "$VERBOSE" = "true" ] && echo "Response: $response"
    else
        print_error "Failed to logout"
        echo "Response: $response"
        return 1
    fi
}

# Main execution
main() {
    print_header "🧪 Namaskah SMS API Testing Suite"
    print_info "Base URL: $BASE_URL"
    print_info "Test Email: $TEST_EMAIL"
    
    # Check server
    check_server
    
    # Run tests
    local passed=0
    local failed=0
    
    tests=(
        "test_health_check"
        "test_list_countries"
        "test_user_registration"
        "test_get_profile"
        "test_get_balance"
        "test_get_services"
        "test_add_credits"
        "test_create_verification"
        "test_check_verification_status"
        "test_get_sms_inbox"
        "test_get_analytics"
        "test_get_payment_history"
        "test_refresh_token"
        "test_update_profile"
        "test_logout"
    )
    
    for test in "${tests[@]}"; do
        if $test; then
            ((passed++))
        else
            ((failed++))
        fi
    done
    
    # Summary
    print_header "📊 Test Summary"
    echo -e "${GREEN}Passed: $passed${NC}"
    echo -e "${RED}Failed: $failed${NC}"
    echo -e "Total: $((passed + failed))"
    
    if [ $failed -eq 0 ]; then
        print_success "All tests passed! 🎉"
        exit 0
    else
        print_error "Some tests failed"
        exit 1
    fi
}

# Run main function
main "$@"
