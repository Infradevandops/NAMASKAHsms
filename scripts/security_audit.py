#!/usr/bin/env python3
"""Security audit script for Namaskah"""
import subprocess
import sys

def run_bandit():
    """Run Bandit security linter"""
    print("🔒 Running Bandit security scan...")
    result = subprocess.run(
        ["bandit", "-r", "app/", "-f", "txt", "-o", "security_report_bandit.txt"],
        capture_output=True
    )
    print(f"✅ Bandit scan complete. Report: security_report_bandit.txt")
    return result.returncode == 0

def run_safety():
    """Run Safety dependency checker"""
    print("🔒 Running Safety dependency check...")
    result = subprocess.run(
        ["safety", "check", "--json", "--output", "security_report_safety.json"],
        capture_output=True
    )
    print(f"✅ Safety check complete. Report: security_report_safety.json")
    return result.returncode == 0

def check_secrets():
    """Check for exposed secrets"""
    print("🔒 Checking for exposed secrets...")
    dangerous_patterns = [
        "password =",
        "api_key =",
        "secret_key =",
        "AWS_SECRET",
        "PAYSTACK_SECRET"
    ]
    
    issues = []
    for pattern in dangerous_patterns:
        result = subprocess.run(
            ["grep", "-r", pattern, "app/", "--exclude-dir=__pycache__"],
            capture_output=True,
            text=True
        )
        if result.stdout:
            issues.append(f"Found '{pattern}' in code")
    
    if issues:
        print(f"⚠️  Found {len(issues)} potential secret exposures")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ No exposed secrets found")
        return True

def main():
    print("=" * 60)
    print("🔒 NAMASKAH SECURITY AUDIT")
    print("=" * 60)
    
    results = {
        "bandit": run_bandit(),
        "safety": run_safety(),
        "secrets": check_secrets()
    }
    
    print("\n" + "=" * 60)
    print("📊 AUDIT SUMMARY")
    print("=" * 60)
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check.capitalize()}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n✅ All security checks passed!")
        return 0
    else:
        print("\n⚠️  Some security checks failed. Review reports.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
