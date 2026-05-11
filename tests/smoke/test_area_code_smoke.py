#!/usr/bin/env python3
"""
Automated smoke tests for area code tier gating feature.
Runs automatically after production deployment to verify functionality.

Usage:
    python3 tests/smoke/test_area_code_smoke.py --env production
    python3 tests/smoke/test_area_code_smoke.py --env staging
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Dict, List, Tuple

import requests


class AreaCodeSmokeTests:
    """Automated smoke tests for area code tier gating."""

    def __init__(self, base_url: str, test_users: Dict[str, Dict]):
        self.base_url = base_url.rstrip("/")
        self.test_users = test_users
        self.results = []
        self.tokens = {}

    def log(self, message: str, level: str = "INFO"):
        """Log test message."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def login(self, tier: str) -> str:
        """Login and get access token for tier."""
        if tier in self.tokens:
            return self.tokens[tier]

        user = self.test_users.get(tier)
        if not user:
            raise ValueError(f"No test user configured for tier: {tier}")

        self.log(f"Logging in as {tier} user: {user['email']}")

        response = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"email": user["email"], "password": user["password"]},
            timeout=10,
        )

        if response.status_code != 200:
            raise Exception(f"Login failed for {tier}: {response.text}")

        token = response.json().get("access_token")
        self.tokens[tier] = token
        return token

    def test_payg_voice_area_code_fee(self) -> Tuple[bool, str]:
        """Test 1: PAYG user charged $0.25 for voice area code."""
        try:
            token = self.login("payg")

            # Get user balance before
            balance_response = requests.get(
                f"{self.base_url}/api/billing/balance",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            balance_before = float(balance_response.json().get("balance", 0))

            # Create voice verification with area code
            response = requests.post(
                f"{self.base_url}/api/verification/request",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "service": "whatsapp",
                    "country": "US",
                    "capability": "voice",
                    "area_codes": ["212"],
                },
                timeout=30,
            )

            if response.status_code != 201:
                return False, f"API returned {response.status_code}: {response.text}"

            data = response.json()

            # Verify fee structure
            if "area_code_fee" not in data:
                return False, "Response missing area_code_fee field"

            if data["area_code_fee"] != 0.25:
                return False, f"Expected fee $0.25, got ${data['area_code_fee']}"

            if "base_cost" not in data:
                return False, "Response missing base_cost field"

            expected_total = data["base_cost"] + 0.25
            if abs(data["cost"] - expected_total) > 0.01:
                return (
                    False,
                    f"Total cost mismatch: expected ${expected_total}, got ${data['cost']}",
                )

            return (
                True,
                f"✅ PAYG voice area code fee correct: ${data['area_code_fee']}",
            )

        except Exception as e:
            return False, f"Test failed with exception: {str(e)}"

    def test_pro_voice_area_code_included(self) -> Tuple[bool, str]:
        """Test 2: Pro user gets voice area code included (no fee)."""
        try:
            token = self.login("pro")

            response = requests.post(
                f"{self.base_url}/api/verification/request",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "service": "whatsapp",
                    "country": "US",
                    "capability": "voice",
                    "area_codes": ["415"],
                },
                timeout=30,
            )

            if response.status_code != 201:
                return False, f"API returned {response.status_code}: {response.text}"

            data = response.json()

            if data.get("area_code_fee", -1) != 0.0:
                return False, f"Expected no fee, got ${data.get('area_code_fee')}"

            if data["cost"] != data.get("base_cost", 0):
                return False, f"Total should equal base cost for Pro tier"

            return True, f"✅ Pro voice area code included (no fee)"

        except Exception as e:
            return False, f"Test failed with exception: {str(e)}"

    def test_freemium_blocked(self) -> Tuple[bool, str]:
        """Test 3: Freemium user blocked from area code selection."""
        try:
            token = self.login("freemium")

            response = requests.post(
                f"{self.base_url}/api/verification/request",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "service": "whatsapp",
                    "country": "US",
                    "capability": "voice",
                    "area_codes": ["212"],
                },
                timeout=30,
            )

            # Should return 402 or 400 error
            if response.status_code in [200, 201]:
                return False, "Freemium user should be blocked from area code selection"

            if response.status_code not in [400, 402]:
                return False, f"Expected 400/402 error, got {response.status_code}"

            return True, f"✅ Freemium correctly blocked from area code"

        except Exception as e:
            return False, f"Test failed with exception: {str(e)}"

    def test_api_response_format(self) -> Tuple[bool, str]:
        """Test 4: API response includes required fields."""
        try:
            token = self.login("payg")

            response = requests.post(
                f"{self.base_url}/api/verification/request",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "service": "whatsapp",
                    "country": "US",
                    "capability": "voice",
                    "area_codes": ["212"],
                },
                timeout=30,
            )

            if response.status_code != 201:
                return False, f"API returned {response.status_code}"

            data = response.json()
            required_fields = [
                "cost",
                "base_cost",
                "area_code_fee",
                "requested_area_code",
                "phone_number",
            ]

            missing_fields = [f for f in required_fields if f not in data]
            if missing_fields:
                return False, f"Missing required fields: {missing_fields}"

            return True, f"✅ API response format correct"

        except Exception as e:
            return False, f"Test failed with exception: {str(e)}"

    def test_health_check(self) -> Tuple[bool, str]:
        """Test 0: Basic health check."""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)

            if response.status_code != 200:
                return False, f"Health check failed: {response.status_code}"

            return True, "✅ API health check passed"

        except Exception as e:
            return False, f"Health check failed: {str(e)}"

    def run_all_tests(self) -> bool:
        """Run all smoke tests."""
        tests = [
            ("Health Check", self.test_health_check),
            ("PAYG Voice Area Code Fee", self.test_payg_voice_area_code_fee),
            ("Pro Voice Area Code Included", self.test_pro_voice_area_code_included),
            ("Freemium Blocked", self.test_freemium_blocked),
            ("API Response Format", self.test_api_response_format),
        ]

        self.log("=" * 60)
        self.log("Area Code Tier Gating - Smoke Tests")
        self.log(f"Environment: {self.base_url}")
        self.log("=" * 60)

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            self.log(f"\nRunning: {test_name}")
            try:
                success, message = test_func()
                if success:
                    self.log(message, "PASS")
                    passed += 1
                else:
                    self.log(message, "FAIL")
                    failed += 1

                self.results.append(
                    {"test": test_name, "passed": success, "message": message}
                )
            except Exception as e:
                self.log(f"Test error: {str(e)}", "ERROR")
                failed += 1
                self.results.append(
                    {"test": test_name, "passed": False, "message": str(e)}
                )

        self.log("\n" + "=" * 60)
        self.log("Test Summary")
        self.log("=" * 60)
        self.log(f"Passed: {passed}/{len(tests)}")
        self.log(f"Failed: {failed}/{len(tests)}")
        self.log(f"Success Rate: {passed/len(tests)*100:.1f}%")

        if failed == 0:
            self.log("\n✅ All smoke tests passed!", "SUCCESS")
            return True
        else:
            self.log(f"\n❌ {failed} test(s) failed", "FAILURE")
            return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Area Code Smoke Tests")
    parser.add_argument(
        "--env",
        choices=["production", "staging", "local"],
        default="staging",
        help="Environment to test",
    )
    parser.add_argument("--url", help="Custom base URL (overrides --env)")

    args = parser.parse_args()

    # Environment URLs
    env_urls = {
        "production": "https://vrenum.onrender.com",
        "staging": "https://vrenum.onrender.com",  # Use production for staging
        "local": "http://localhost:8000",
    }

    base_url = args.url or env_urls[args.env]

    # Test users (configure these for your environment)
    test_users = {
        "freemium": {"email": "freemium@test.com", "password": "test123"},
        "payg": {"email": "payg@test.com", "password": "test123"},
        "pro": {"email": "pro@test.com", "password": "test123"},
        "custom": {"email": "custom@test.com", "password": "test123"},
    }

    # Run tests
    tester = AreaCodeSmokeTests(base_url, test_users)
    success = tester.run_all_tests()

    # Save results
    results_file = (
        f"smoke_test_results_{args.env}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(results_file, "w") as f:
        json.dump(
            {
                "environment": args.env,
                "base_url": base_url,
                "timestamp": datetime.now().isoformat(),
                "results": tester.results,
            },
            f,
            indent=2,
        )

    print(f"\nResults saved to: {results_file}")

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
