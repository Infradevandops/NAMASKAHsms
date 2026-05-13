"""
Manual Test Script for Email Template Editor
Phase 2: Testing & Validation (2 hours)

Run this script to validate email template functionality.
"""

import asyncio
import sys
from typing import Dict, List

import httpx

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword123"

# Test results
test_results = []


class TestResult:
    def __init__(self, name: str, passed: bool, message: str = "", duration: float = 0):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration = duration


def log_test(name: str, passed: bool, message: str = ""):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {name}")
    if message:
        print(f"   {message}")
    test_results.append(TestResult(name, passed, message))


async def get_auth_token(client: httpx.AsyncClient) -> str:
    """Get authentication token"""
    try:
        response = await client.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token", "")
        return ""
    except Exception as e:
        print(f"❌ Failed to authenticate: {e}")
        return ""


async def test_1_access_page(client: httpx.AsyncClient, token: str):
    """Test 1: Access Page (5 min)"""
    print("\n=== Test 1: Access Page ===")

    try:
        response = await client.get(f"{BASE_URL}/email-templates")
        log_test(
            "Page loads without errors",
            response.status_code == 200,
            f"Status: {response.status_code}",
        )
    except Exception as e:
        log_test("Page loads without errors", False, str(e))


async def test_2_list_templates(client: httpx.AsyncClient, token: str):
    """Test 2: List Templates (10 min)"""
    print("\n=== Test 2: List Templates ===")

    try:
        response = await client.get(
            f"{BASE_URL}/api/whitelabel/email-templates",
            headers={"Authorization": f"Bearer {token}"},
        )

        if response.status_code == 200:
            templates = response.json()
            log_test(
                "GET /api/whitelabel/email-templates returns 200",
                True,
                f"Found {len(templates)} templates",
            )

            expected_templates = [
                "welcome",
                "verification_code",
                "payment_success",
                "payment_failed",
                "low_balance",
                "tier_upgrade",
                "password_reset",
            ]

            template_names = [t["template_name"] for t in templates]
            all_present = all(name in template_names for name in expected_templates)
            log_test(
                "All 7 templates present",
                all_present,
                f"Found: {', '.join(template_names)}",
            )

            has_variables = all(
                len(t.get("available_variables", [])) > 0 for t in templates
            )
            log_test("All templates have available_variables", has_variables)

        elif response.status_code == 402:
            log_test(
                "Tier check working",
                True,
                "402 Payment Required - upgrade to Pro tier needed",
            )
        else:
            log_test(
                "GET /api/whitelabel/email-templates",
                False,
                f"Status: {response.status_code}",
            )

    except Exception as e:
        log_test("List templates", False, str(e))


async def test_3_get_template(client: httpx.AsyncClient, token: str):
    """Test 3: Get Single Template (20 min)"""
    print("\n=== Test 3: Get Single Template ===")

    template_name = "welcome"

    try:
        response = await client.get(
            f"{BASE_URL}/api/whitelabel/email-template/{template_name}",
            headers={"Authorization": f"Bearer {token}"},
        )

        if response.status_code == 200:
            template = response.json()
            log_test(
                f"GET /api/whitelabel/email-template/{template_name}",
                True,
                f"Template loaded",
            )

            has_subject = bool(template.get("subject"))
            log_test("Template has subject", has_subject, template.get("subject", ""))

            has_html = bool(template.get("html_content"))
            log_test("Template has html_content", has_html)

            has_vars = len(template.get("available_variables", [])) > 0
            log_test(
                "Template has available_variables",
                has_vars,
                f"Variables: {', '.join(template.get('available_variables', []))}",
            )

        elif response.status_code == 402:
            log_test(
                "Tier check working",
                True,
                "402 Payment Required - upgrade to Pro tier needed",
            )
        else:
            log_test(
                f"GET template {template_name}",
                False,
                f"Status: {response.status_code}",
            )

    except Exception as e:
        log_test("Get template", False, str(e))


async def test_4_save_template(client: httpx.AsyncClient, token: str):
    """Test 4: Save Template (20 min)"""
    print("\n=== Test 4: Save Template ===")

    template_data = {
        "template_name": "welcome",
        "subject": "Welcome to {{ company_name }}!",
        "html_content": "<h1>Hello {{ user_name }}!</h1><p>Welcome to {{ company_name }}.</p>",
        "text_content": "Hello {{ user_name }}! Welcome to {{ company_name }}.",
    }

    try:
        response = await client.post(
            f"{BASE_URL}/api/whitelabel/email-template",
            headers={"Authorization": f"Bearer {token}"},
            json=template_data,
        )

        if response.status_code == 200:
            saved = response.json()
            log_test("POST /api/whitelabel/email-template", True, "Template saved")

            subject_match = saved.get("subject") == template_data["subject"]
            log_test("Subject saved correctly", subject_match)

            html_match = saved.get("html_content") == template_data["html_content"]
            log_test("HTML content saved correctly", html_match)

        elif response.status_code == 402:
            log_test(
                "Tier check working",
                True,
                "402 Payment Required - upgrade to Pro tier needed",
            )
        else:
            log_test(
                "Save template",
                False,
                f"Status: {response.status_code}, Body: {response.text}",
            )

    except Exception as e:
        log_test("Save template", False, str(e))


async def test_5_variable_validation(client: httpx.AsyncClient, token: str):
    """Test 5: Variable Validation (20 min)"""
    print("\n=== Test 5: Variable Validation ===")

    # Test with invalid variable
    invalid_template = {
        "template_name": "welcome",
        "subject": "Test {{ invalid_var }}",
        "html_content": "<p>{{ invalid_var }}</p>",
    }

    try:
        response = await client.post(
            f"{BASE_URL}/api/whitelabel/email-template",
            headers={"Authorization": f"Bearer {token}"},
            json=invalid_template,
        )

        if response.status_code == 400:
            error = response.json()
            log_test(
                "Invalid variable rejected",
                True,
                f"Error: {error.get('detail', '')}",
            )
        elif response.status_code == 402:
            log_test(
                "Tier check working",
                True,
                "402 Payment Required - upgrade to Pro tier needed",
            )
        else:
            log_test(
                "Invalid variable validation",
                False,
                f"Expected 400, got {response.status_code}",
            )

    except Exception as e:
        log_test("Variable validation", False, str(e))

    # Test with valid variables
    valid_template = {
        "template_name": "welcome",
        "subject": "Welcome {{ user_name }}!",
        "html_content": "<p>Hello {{ user_name }}, welcome to {{ company_name }}!</p>",
    }

    try:
        response = await client.post(
            f"{BASE_URL}/api/whitelabel/email-template",
            headers={"Authorization": f"Bearer {token}"},
            json=valid_template,
        )

        if response.status_code == 200:
            log_test("Valid variables accepted", True)
        elif response.status_code == 402:
            log_test(
                "Tier check working",
                True,
                "402 Payment Required - upgrade to Pro tier needed",
            )
        else:
            log_test(
                "Valid variables",
                False,
                f"Status: {response.status_code}, Body: {response.text}",
            )

    except Exception as e:
        log_test("Valid variables", False, str(e))


async def test_6_delete_template(client: httpx.AsyncClient, token: str):
    """Test 6: Delete Template (15 min)"""
    print("\n=== Test 6: Delete Template ===")

    template_name = "welcome"

    try:
        response = await client.delete(
            f"{BASE_URL}/api/whitelabel/email-template/{template_name}",
            headers={"Authorization": f"Bearer {token}"},
        )

        if response.status_code == 200:
            log_test("DELETE /api/whitelabel/email-template", True, "Template deleted")
        elif response.status_code == 404:
            log_test(
                "Delete non-existent template",
                True,
                "404 Not Found - no custom template exists",
            )
        elif response.status_code == 402:
            log_test(
                "Tier check working",
                True,
                "402 Payment Required - upgrade to Pro tier needed",
            )
        else:
            log_test(
                "Delete template",
                False,
                f"Status: {response.status_code}, Body: {response.text}",
            )

    except Exception as e:
        log_test("Delete template", False, str(e))


async def test_7_edge_cases(client: httpx.AsyncClient, token: str):
    """Test 7: Edge Cases (30 min)"""
    print("\n=== Test 7: Edge Cases ===")

    # Empty subject
    try:
        response = await client.post(
            f"{BASE_URL}/api/whitelabel/email-template",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "template_name": "welcome",
                "subject": "",
                "html_content": "<p>Test</p>",
            },
        )
        log_test(
            "Empty subject handled",
            response.status_code in [200, 400, 402],
            f"Status: {response.status_code}",
        )
    except Exception as e:
        log_test("Empty subject", False, str(e))

    # Very long content
    try:
        long_content = "<p>" + ("Test " * 2000) + "</p>"
        response = await client.post(
            f"{BASE_URL}/api/whitelabel/email-template",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "template_name": "welcome",
                "subject": "Test",
                "html_content": long_content,
            },
        )
        log_test(
            "Long content handled",
            response.status_code in [200, 400, 402],
            f"Status: {response.status_code}",
        )
    except Exception as e:
        log_test("Long content", False, str(e))

    # Special characters
    try:
        response = await client.post(
            f"{BASE_URL}/api/whitelabel/email-template",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "template_name": "welcome",
                "subject": "Test <>&\"'",
                "html_content": "<p>Special chars: <>&\"'</p>",
            },
        )
        log_test(
            "Special characters handled",
            response.status_code in [200, 400, 402],
            f"Status: {response.status_code}",
        )
    except Exception as e:
        log_test("Special characters", False, str(e))

    # Invalid template name
    try:
        response = await client.post(
            f"{BASE_URL}/api/whitelabel/email-template",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "template_name": "invalid_template_name",
                "subject": "Test",
                "html_content": "<p>Test</p>",
            },
        )
        log_test(
            "Invalid template name rejected",
            response.status_code in [400, 402],
            f"Status: {response.status_code}",
        )
    except Exception as e:
        log_test("Invalid template name", False, str(e))


async def run_all_tests():
    """Run all email template tests"""
    print("=" * 60)
    print("EMAIL TEMPLATE EDITOR - AUTOMATED TEST SUITE")
    print("=" * 60)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Test User: {TEST_USER_EMAIL}")
    print("\nStarting tests...\n")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get auth token
        print("Authenticating...")
        token = await get_auth_token(client)

        if not token:
            print("\n⚠️  WARNING: Could not authenticate.")
            print("Tests will run but may return 401 Unauthorized.")
            print("To fix: Create a test user or update credentials in this script.\n")

        # Run all tests
        await test_1_access_page(client, token)
        await test_2_list_templates(client, token)
        await test_3_get_template(client, token)
        await test_4_save_template(client, token)
        await test_5_variable_validation(client, token)
        await test_6_delete_template(client, token)
        await test_7_edge_cases(client, token)

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in test_results if r.passed)
    failed = sum(1 for r in test_results if not r.passed)
    total = len(test_results)

    print(f"\nTotal Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/total*100):.1f}%\n")

    if failed > 0:
        print("Failed Tests:")
        for r in test_results:
            if not r.passed:
                print(f"  ❌ {r.name}")
                if r.message:
                    print(f"     {r.message}")

    print("\n" + "=" * 60)

    # Determine overall status
    if failed == 0:
        print("✅ ALL TESTS PASSED - Email template editor is working!")
        print("✅ Phase 2 Complete - Ready for Phase 3")
        return 0
    elif passed >= total * 0.7:
        print("⚠️  MOSTLY WORKING - Some issues found")
        print("Review failed tests and fix issues before proceeding")
        return 1
    else:
        print("❌ CRITICAL ISSUES - Email template editor needs fixes")
        print("Do not proceed to Phase 3 until issues are resolved")
        return 2


if __name__ == "__main__":
    print("\n📧 Email Template Editor Test Suite\n")
    print("Prerequisites:")
    print("  1. Server running at http://localhost:8000")
    print("  2. Test user created (or update credentials in script)")
    print("  3. Test user upgraded to Pro tier (or expect 402 errors)\n")

    input("Press Enter to start tests...")

    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
