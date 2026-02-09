#!/usr/bin/env python3
"""
Phase 2 Verification Script
Tests that all dashboard pages are accessible and JavaScript is wired correctly
"""

import requests
import sys
from typing import List, Dict

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword123"

# Pages to test
DASHBOARD_PAGES = [
    {"name": "Dashboard", "path": "/dashboard", "requires_auth": True},
    {"name": "Analytics", "path": "/analytics", "requires_auth": True},
    {"name": "Wallet", "path": "/wallet", "requires_auth": True},
    {"name": "History", "path": "/history", "requires_auth": True},
    {"name": "Notifications", "path": "/notifications", "requires_auth": True},
    {"name": "Verify", "path": "/verify", "requires_auth": True},
    {"name": "Settings", "path": "/settings", "requires_auth": True},
    {"name": "Webhooks", "path": "/webhooks", "requires_auth": True},
    {"name": "Referrals", "path": "/referrals", "requires_auth": True},
]

# API endpoints to test
API_ENDPOINTS = [
    {"name": "Analytics Summary", "path": "/api/analytics/summary", "method": "GET"},
    {"name": "Wallet Balance", "path": "/api/billing/balance", "method": "GET"},
    {"name": "Wallet Transactions", "path": "/api/billing/history", "method": "GET"},
    {"name": "Verification History", "path": "/api/v1/verify/history", "method": "GET"},
    {"name": "Notifications", "path": "/api/notifications", "method": "GET"},
    {"name": "User Profile", "path": "/api/v1/user/me", "method": "GET"},
    {"name": "Webhooks", "path": "/api/webhooks", "method": "GET"},
    {"name": "Referral Stats", "path": "/api/referrals/stats", "method": "GET"},
    {"name": "Current Tier", "path": "/api/tiers/current", "method": "GET"},
]


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


def login() -> str:
    """Login and get access token"""
    print_info("Attempting to login...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                print_success("Login successful")
                return token
            else:
                print_error("No access token in response")
                return None
        else:
            print_warning(f"Login failed with status {response.status_code}")
            print_warning("Continuing without authentication (some tests will fail)")
            return None
            
    except requests.exceptions.RequestException as e:
        print_error(f"Login request failed: {e}")
        return None


def test_page_accessibility(session: requests.Session) -> Dict[str, bool]:
    """Test that all dashboard pages are accessible"""
    print_header("Testing Page Accessibility")
    
    results = {}
    
    for page in DASHBOARD_PAGES:
        try:
            response = session.get(f"{BASE_URL}{page['path']}", timeout=10)
            
            if response.status_code == 200:
                print_success(f"{page['name']}: Accessible (200 OK)")
                results[page['name']] = True
            elif response.status_code == 302:
                print_warning(f"{page['name']}: Redirect (302) - Requires authentication")
                results[page['name']] = False
            else:
                print_error(f"{page['name']}: Failed ({response.status_code})")
                results[page['name']] = False
                
        except requests.exceptions.RequestException as e:
            print_error(f"{page['name']}: Request failed - {e}")
            results[page['name']] = False
    
    return results


def test_api_endpoints(session: requests.Session) -> Dict[str, bool]:
    """Test that all API endpoints are accessible"""
    print_header("Testing API Endpoints")
    
    results = {}
    
    for endpoint in API_ENDPOINTS:
        try:
            if endpoint['method'] == 'GET':
                response = session.get(f"{BASE_URL}{endpoint['path']}", timeout=10)
            else:
                response = session.post(f"{BASE_URL}{endpoint['path']}", timeout=10)
            
            if response.status_code in [200, 201]:
                print_success(f"{endpoint['name']}: Working ({response.status_code})")
                results[endpoint['name']] = True
            elif response.status_code == 401:
                print_warning(f"{endpoint['name']}: Requires authentication (401)")
                results[endpoint['name']] = False
            elif response.status_code == 404:
                print_error(f"{endpoint['name']}: Not found (404)")
                results[endpoint['name']] = False
            else:
                print_warning(f"{endpoint['name']}: Status {response.status_code}")
                results[endpoint['name']] = False
                
        except requests.exceptions.RequestException as e:
            print_error(f"{endpoint['name']}: Request failed - {e}")
            results[endpoint['name']] = False
    
    return results


def test_javascript_files() -> Dict[str, bool]:
    """Test that JavaScript files are accessible"""
    print_header("Testing JavaScript Files")
    
    js_files = [
        "/static/js/dashboard.js",
        "/static/js/verification.js",
        "/static/js/api-retry.js",
        "/static/js/frontend-logger.js",
    ]
    
    results = {}
    
    for js_file in js_files:
        try:
            response = requests.get(f"{BASE_URL}{js_file}", timeout=10)
            
            if response.status_code == 200:
                print_success(f"{js_file}: Accessible")
                results[js_file] = True
            else:
                print_error(f"{js_file}: Failed ({response.status_code})")
                results[js_file] = False
                
        except requests.exceptions.RequestException as e:
            print_error(f"{js_file}: Request failed - {e}")
            results[js_file] = False
    
    return results


def print_summary(page_results: Dict, api_results: Dict, js_results: Dict):
    """Print test summary"""
    print_header("Test Summary")
    
    total_tests = len(page_results) + len(api_results) + len(js_results)
    passed_tests = sum([
        sum(page_results.values()),
        sum(api_results.values()),
        sum(js_results.values())
    ])
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {Colors.GREEN}{passed_tests}{Colors.RESET}")
    print(f"Failed: {Colors.RED}{total_tests - passed_tests}{Colors.RESET}")
    print(f"Success Rate: {(passed_tests / total_tests * 100):.1f}%\n")
    
    if passed_tests == total_tests:
        print_success("All tests passed! ✨")
        return 0
    else:
        print_warning(f"{total_tests - passed_tests} test(s) failed")
        return 1


def main():
    """Main test runner"""
    print_header("Phase 2 Verification Script")
    print_info(f"Testing against: {BASE_URL}")
    
    # Create session
    session = requests.Session()
    
    # Try to login
    token = login()
    if token:
        session.headers.update({"Authorization": f"Bearer {token}"})
    
    # Run tests
    page_results = test_page_accessibility(session)
    api_results = test_api_endpoints(session)
    js_results = test_javascript_files()
    
    # Print summary
    exit_code = print_summary(page_results, api_results, js_results)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_warning("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nUnexpected error: {e}")
        sys.exit(1)
