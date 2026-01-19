#!/usr/bin/env python3
"""Security test runner script."""
import subprocess
import sys
from pathlib import Path


def run_security_tests():
    """Run all security tests."""
    print("🛡️ Running comprehensive security tests...\n")

    project_root = Path(__file__).parent.parent

    # Test categories to run
    test_categories = [
        ("SQL Injection Tests", "app/tests/test_sql_injection.py"),
        ("XSS Prevention Tests", "app/tests/test_xss_prevention.py"),
        ("Log Injection Tests", "app/tests/test_log_injection.py"),
        ("Comprehensive Security Tests", "app/tests/test_security_comprehensive.py"),
    ]

    results = {}

    for category, test_file in test_categories:
        print(f"🔍 Running {category}...")

        test_path = project_root / test_file
        if not test_path.exists():
            print(f"⚠️ Test file not found: {test_file}")
            results[category] = "SKIPPED"
            continue

        try:
            # Run pytest for the specific test file
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_path), "-v"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                print(f"✅ {category}: PASSED")
                results[category] = "PASSED"
            else:
                print(f"❌ {category}: FAILED")
                print(f"Error output: {result.stdout[-200:]}")
                results[category] = "FAILED"

        except subprocess.TimeoutExpired:
            print(f"⏰ {category}: TIMEOUT")
            results[category] = "TIMEOUT"
        except Exception as e:
            print(f"💥 {category}: ERROR - {e}")
            results[category] = "ERROR"

    # Run security scan
    print(f"\n🔍 Running automated security scan...")
    try:
        scan_script = project_root / "scripts" / "security_scan.py"
        result = subprocess.run(
            [sys.executable, str(scan_script), str(project_root)],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            print("✅ Security scan: PASSED")
            results["Security Scan"] = "PASSED"
        else:
            print("❌ Security scan: ISSUES FOUND")
            print(result.stdout[-300:])
            results["Security Scan"] = "FAILED"

    except Exception as e:
        print(f"💥 Security scan: ERROR - {e}")
        results["Security Scan"] = "ERROR"

    # Print summary
    print(f"\n📊 Security Test Summary:")
    print("=" * 50)

    passed = sum(1 for status in results.values() if status == "PASSED")
    total = len(results)

    for category, status in results.items():
        status_icon = {
            "PASSED": "✅",
            "FAILED": "❌",
            "SKIPPED": "⚠️",
            "TIMEOUT": "⏰",
            "ERROR": "💥",
        }.get(status, "❓")

        print(f"{status_icon} {category}: {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    # Return exit code
    if passed == total:
        print("\n🎉 All security tests passed!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} security tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(run_security_tests())
