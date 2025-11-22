#!/usr/bin/env python3
"""Phase 5: Comprehensive Testing & Documentation Script"""

import subprocess
import sys
import os
from pathlib import Path
import json
import time

def run_command(cmd, cwd=None, capture_output=True):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=capture_output, 
            text=True, timeout=300
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def install_missing_packages():
    """Install missing packages required for testing."""
    print("📦 Installing missing packages...")
    
    packages = [
        "pytest-cov",
        "pytest-asyncio", 
        "httpx",
        "textverified",
        "prometheus_client",
        "pytz"
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        success, stdout, stderr = run_command(f"pip3 install {package}")
        if not success:
            print(f"⚠️ Failed to install {package}: {stderr}")
        else:
            print(f"✅ Installed {package}")

def run_unit_tests():
    """Run unit tests and collect coverage."""
    print("\n🧪 Running Unit Tests...")
    
    # Run tests with coverage
    cmd = "python3 -m pytest app/tests/ -v --tb=short --cov=app --cov-report=term-missing --cov-report=json --maxfail=10"
    success, stdout, stderr = run_command(cmd)
    
    if success:
        print("✅ Unit tests passed")
        
        # Parse coverage report
        try:
            with open("coverage.json", "r") as f:
                coverage_data = json.load(f)
                coverage_percent = coverage_data["totals"]["percent_covered"]
                print(f"📊 Test Coverage: {coverage_percent:.1f}%")
                return True, coverage_percent
        except:
            print("⚠️ Could not parse coverage report")
            return True, 0
    else:
        print(f"❌ Unit tests failed:\n{stderr}")
        return False, 0

def run_integration_tests():
    """Run integration tests."""
    print("\n🔗 Running Integration Tests...")
    
    # Run specific integration tests
    integration_tests = [
        "app/tests/test_integration_comprehensive.py",
        "app/tests/test_api_integration.py",
        "app/tests/test_provider_integration.py"
    ]
    
    passed = 0
    total = len(integration_tests)
    
    for test_file in integration_tests:
        if os.path.exists(test_file):
            cmd = f"python3 -m pytest {test_file} -v --tb=short"
            success, stdout, stderr = run_command(cmd)
            if success:
                print(f"✅ {test_file}")
                passed += 1
            else:
                print(f"❌ {test_file}: {stderr}")
        else:
            print(f"⚠️ {test_file} not found")
    
    print(f"📊 Integration Tests: {passed}/{total} passed")
    return passed == total

def run_security_tests():
    """Run security tests."""
    print("\n🔒 Running Security Tests...")
    
    security_tests = [
        "app/tests/test_security_comprehensive.py",
        "app/tests/test_sql_injection.py", 
        "app/tests/test_xss_prevention.py",
        "app/tests/test_path_traversal.py"
    ]
    
    passed = 0
    total = len(security_tests)
    
    for test_file in security_tests:
        if os.path.exists(test_file):
            cmd = f"python3 -m pytest {test_file} -v --tb=short"
            success, stdout, stderr = run_command(cmd)
            if success:
                print(f"✅ {test_file}")
                passed += 1
            else:
                print(f"❌ {test_file}: {stderr}")
        else:
            print(f"⚠️ {test_file} not found")
    
    print(f"📊 Security Tests: {passed}/{total} passed")
    return passed == total

def run_performance_tests():
    """Run basic performance tests."""
    print("\n⚡ Running Performance Tests...")
    
    # Simple load test
    cmd = "python3 scripts/load_test.py --requests=100 --concurrency=10"
    if os.path.exists("scripts/load_test.py"):
        success, stdout, stderr = run_command(cmd)
        if success:
            print("✅ Performance tests passed")
            return True
        else:
            print(f"❌ Performance tests failed: {stderr}")
            return False
    else:
        print("⚠️ Load test script not found, skipping performance tests")
        return True

def validate_code_quality():
    """Validate code quality metrics."""
    print("\n📏 Validating Code Quality...")
    
    # Run flake8 for style check
    cmd = "python3 -m flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics"
    success, stdout, stderr = run_command(cmd)
    
    if success and not stdout.strip():
        print("✅ No critical code quality issues found")
        return True
    else:
        print(f"⚠️ Code quality issues found:\n{stdout}")
        return False

def generate_test_report():
    """Generate comprehensive test report."""
    print("\n📋 Generating Test Report...")
    
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "phase": "Phase 5 - Testing & Documentation",
        "tests": {
            "unit_tests": {"status": "pending"},
            "integration_tests": {"status": "pending"}, 
            "security_tests": {"status": "pending"},
            "performance_tests": {"status": "pending"}
        },
        "coverage": {"percent": 0},
        "quality": {"status": "pending"}
    }
    
    # Run all tests and collect results
    unit_success, coverage = run_unit_tests()
    report["tests"]["unit_tests"]["status"] = "passed" if unit_success else "failed"
    report["coverage"]["percent"] = coverage
    
    integration_success = run_integration_tests()
    report["tests"]["integration_tests"]["status"] = "passed" if integration_success else "failed"
    
    security_success = run_security_tests()
    report["tests"]["security_tests"]["status"] = "passed" if security_success else "failed"
    
    performance_success = run_performance_tests()
    report["tests"]["performance_tests"]["status"] = "passed" if performance_success else "failed"
    
    quality_success = validate_code_quality()
    report["quality"]["status"] = "passed" if quality_success else "failed"
    
    # Save report
    with open("PHASE_5_TEST_REPORT.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "="*50)
    print("📊 PHASE 5 TEST SUMMARY")
    print("="*50)
    print(f"Unit Tests: {'✅ PASSED' if unit_success else '❌ FAILED'}")
    print(f"Integration Tests: {'✅ PASSED' if integration_success else '❌ FAILED'}")
    print(f"Security Tests: {'✅ PASSED' if security_success else '❌ FAILED'}")
    print(f"Performance Tests: {'✅ PASSED' if performance_success else '❌ FAILED'}")
    print(f"Code Quality: {'✅ PASSED' if quality_success else '❌ FAILED'}")
    print(f"Test Coverage: {coverage:.1f}%")
    print("="*50)
    
    overall_success = all([
        unit_success, integration_success, security_success, 
        performance_success, quality_success, coverage >= 80
    ])
    
    if overall_success:
        print("🎉 ALL TESTS PASSED - Phase 5 Complete!")
    else:
        print("⚠️ Some tests failed - Review required")
    
    return overall_success

def main():
    """Main testing function."""
    print("🚀 Starting Phase 5: Comprehensive Testing & Documentation")
    print("="*60)
    
    # Change to project directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Install missing packages
    install_missing_packages()
    
    # Generate comprehensive test report
    success = generate_test_report()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())