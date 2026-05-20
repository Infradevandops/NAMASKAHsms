#!/usr/bin/env python3
"""Analyze test failures and generate actionable report."""

import subprocess
import sys
from pathlib import Path

def main():
    print("=== Test Suite Analysis ===\n")
    
    # Run tests with minimal output
    print("Running test suite...")
    result = subprocess.run(
        ["python3", "-m", "pytest", "tests/", "--tb=no", "-q"],
        capture_output=True,
        text=True,
        timeout=600
    )
    
    output = result.stdout + result.stderr
    
    # Extract summary
    import re
    match = re.search(r'(\d+) failed, (\d+) passed.*?(\d+) error', output)
    
    if match:
        failed = int(match.group(1))
        passed = int(match.group(2))
        errors = int(match.group(3))
        total = failed + passed
        pass_rate = (passed / total) * 100
        
        print(f"\n📊 Current Status:")
        print(f"   Passed: {passed}/{total} ({pass_rate:.1f}%)")
        print(f"   Failed: {failed}")
        print(f"   Errors: {errors}")
        print(f"   Target: {int(total * 0.95)} passing (95%)")
        print(f"   Gap: {int(total * 0.95) - passed} tests\n")
        
        # Save report
        with open("test_analysis.txt", "w") as f:
            f.write(output)
        
        print("✅ Full output saved to test_analysis.txt")
        
        return 0 if pass_rate >= 95 else 1
    else:
        print("❌ Could not parse test results")
        return 1

if __name__ == "__main__":
    sys.exit(main())
