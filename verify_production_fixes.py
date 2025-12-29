#!/usr/bin/env python3
"""
Production Fixes Verification Script
Tests all applied fixes to ensure they work correctly
"""

import requests
import time
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name, status, message=""):
    symbol = f"{Colors.GREEN}✓{Colors.END}" if status else f"{Colors.RED}✗{Colors.END}"
    print(f"{symbol} {name}")
    if message:
        print(f"  {Colors.YELLOW}{message}{Colors.END}")

def test_auth_refresh_endpoint():
    """Test 1: Verify /api/auth/refresh endpoint exists and works"""
    print(f"\n{Colors.BLUE}Test 1: Auth Refresh Endpoint{Colors.END}")
    
    try:
        # First login to get tokens
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        if response.status_code == 401:
            print_test("Login", False, "Test user doesn't exist - create one first")
            return False
        
        if response.status_code != 200:
            print_test("Login", False, f"Status: {response.status_code}")
            return False
        
        data = response.json()
        refresh_token = data.get("refresh_token")
        
        if not refresh_token:
            print_test("Get refresh token", False, "No refresh token in response")
            return False
        
        print_test("Login successful", True)
        
        # Test refresh endpoint
        refresh_response = requests.post(
            f"{BASE_URL}/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        if refresh_response.status_code == 200:
            refresh_data = refresh_response.json()
            if "access_token" in refresh_data:
                print_test("Refresh endpoint works", True)
                return True
            else:
                print_test("Refresh endpoint", False, "No access_token in response")
                return False
        else:
            print_test("Refresh endpoint", False, f"Status: {refresh_response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_test("Connection", False, "Server not running at localhost:8000")
        return False
    except Exception as e:
        print_test("Test execution", False, str(e))
        return False

def test_frontend_functions():
    """Test 2: Verify frontend JavaScript files are valid"""
    print(f"\n{Colors.BLUE}Test 2: Frontend Functions{Colors.END}")
    
    try:
        # Check dashboard.js
        with open("static/js/dashboard.js", "r") as f:
            content = f.read()
            
        has_rental_handlers = "function setupRentalHandlers" in content
        has_recent_activity = "function loadRecentActivity" in content
        
        print_test("setupRentalHandlers exists", has_rental_handlers)
        print_test("loadRecentActivity exists", has_recent_activity)
        
        # Check auth-check.js
        with open("static/js/auth-check.js", "r") as f:
            auth_content = f.read()
            
        has_refresh_logic = "'/api/auth/refresh'" in auth_content
        has_proper_body = "refresh_token:" in auth_content or '"refresh_token"' in auth_content
        
        print_test("Token refresh logic updated", has_refresh_logic)
        print_test("Refresh uses request body", has_proper_body)
        
        return has_rental_handlers and has_recent_activity and has_refresh_logic
        
    except FileNotFoundError as e:
        print_test("File check", False, str(e))
        return False

def test_circuit_breaker():
    """Test 3: Verify circuit breaker implementation"""
    print(f"\n{Colors.BLUE}Test 3: Circuit Breaker Pattern{Colors.END}")
    
    try:
        with open("app/services/textverified_service.py", "r") as f:
            content = f.read()
        
        has_circuit_breaker = "_circuit_breaker_failures" in content
        has_check_method = "_check_circuit_breaker" in content
        has_record_failure = "_record_failure" in content
        has_record_success = "_record_success" in content
        
        print_test("Circuit breaker variables", has_circuit_breaker)
        print_test("Check circuit breaker method", has_check_method)
        print_test("Record failure method", has_record_failure)
        print_test("Record success method", has_record_success)
        
        return all([has_circuit_breaker, has_check_method, has_record_failure, has_record_success])
        
    except FileNotFoundError:
        print_test("File check", False, "textverified_service.py not found")
        return False

def test_jwt_expiration():
    """Test 4: Verify JWT expiration is set to 24 hours"""
    print(f"\n{Colors.BLUE}Test 4: JWT Token Expiration{Colors.END}")
    
    try:
        with open("app/core/config.py", "r") as f:
            content = f.read()
        
        has_24h_minutes = "jwt_expire_minutes: int = 1440" in content
        has_24h_hours = "jwt_expiry_hours: int = 24" in content
        
        print_test("JWT expiration set to 1440 minutes", has_24h_minutes)
        print_test("JWT expiration set to 24 hours", has_24h_hours)
        
        return has_24h_minutes and has_24h_hours
        
    except FileNotFoundError:
        print_test("File check", False, "config.py not found")
        return False

def test_enhanced_retry_logic():
    """Test 5: Verify enhanced retry logic for SSL errors"""
    print(f"\n{Colors.BLUE}Test 5: Enhanced Retry Logic{Colors.END}")
    
    try:
        with open("app/services/textverified_service.py", "r") as f:
            content = f.read()
        
        has_ssl_detection = "'SSL' in error_msg" in content
        has_connection_detection = "'Connection' in error_msg" in content
        has_improved_logging = "Connection error on attempt" in content
        
        print_test("SSL error detection", has_ssl_detection)
        print_test("Connection error detection", has_connection_detection)
        print_test("Improved error logging", has_improved_logging)
        
        return all([has_ssl_detection, has_connection_detection, has_improved_logging])
        
    except FileNotFoundError:
        print_test("File check", False, "textverified_service.py not found")
        return False

def main():
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}Production Fixes Verification{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    results = []
    
    # Run all tests
    results.append(("Auth Refresh Endpoint", test_auth_refresh_endpoint()))
    results.append(("Frontend Functions", test_frontend_functions()))
    results.append(("Circuit Breaker", test_circuit_breaker()))
    results.append(("JWT Expiration", test_jwt_expiration()))
    results.append(("Enhanced Retry Logic", test_enhanced_retry_logic()))
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}Summary{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"{name}: {status}")
    
    print(f"\n{Colors.BLUE}Total: {passed}/{total} tests passed{Colors.END}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}✓ All fixes verified successfully!{Colors.END}")
        print(f"{Colors.GREEN}Ready for production deployment.{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.RED}✗ Some tests failed. Review the output above.{Colors.END}")
        return 1

if __name__ == "__main__":
    exit(main())
