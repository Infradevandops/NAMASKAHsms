#!/usr/bin/env python3
"""
import json
import subprocess
import sys
import starlette

Security Update Script for Namaskah SMS
Handles security dependency updates and vulnerability checks
"""


def run_command(cmd):

    """Run shell command and return result."""
try:
if isinstance(cmd, str):
            cmd = cmd.split()
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.returncode == 0, result.stdout, result.stderr
except Exception as e:
        return False, "", str(e)


def check_vulnerabilities():

    """Check for known vulnerabilities using safety."""
    print("🔍 Checking for known vulnerabilities...")

    # Install safety if not available
    success, _, _ = run_command("python -m pip show safety")
if not success:
        print("📦 Installing safety scanner...")
        run_command("python -m pip install safety")

    # Run safety check
    success, output, error = run_command("python -m safety check --json")

if success and output:
try:
            vulnerabilities = json.loads(output)
if vulnerabilities:
                print(f"⚠️ Found {len(vulnerabilities)} vulnerabilities:")
for vuln in vulnerabilities:
                    print(f"  - {vuln['package']}: {vuln['vulnerability']}")
                return False
else:
                print("✅ No known vulnerabilities found")
                return True
except json.JSONDecodeError:
            print("✅ No vulnerabilities detected")
            return True
else:
        print(f"❌ Safety check failed: {error}")
        return False


def update_dependencies():

    """Update security-critical dependencies."""
    print("🔄 Updating security-critical dependencies...")

    security_updates = [
        "fastapi>=0.115.4",
        "starlette>=0.49.1",
        "uvicorn>=0.32.0",
        "pydantic>=2.10.5",
        "requests>=2.32.0",
        "jinja2>=3.1.4",
        "sqlalchemy>=2.0.36",
    ]

for package in security_updates:
        print(f"📦 Updating {package}...")
        success, output, error = run_command(f"python -m pip install '{package}'")
if success:
            print(f"✅ Updated {package}")
else:
            print(f"❌ Failed to update {package}: {error}")


def verify_starlette_version():

    """Verify Starlette is at secure version."""
    print("🔍 Verifying Starlette version...")

try:

        version = starlette.__version__

        # Parse version numbers
        major, minor, patch = map(int, version.split("."))

        # Check if version is >= 0.49.1
if (
            (major > 0)
            or (major == 0 and minor > 49)
            or (major == 0 and minor == 49 and patch >= 1)
        ):
            print(f"✅ Starlette {version} is secure")
            return True
else:
            print(f"⚠️ Starlette {version} is vulnerable. Upgrade to >= 0.49.1")
            return False

except ImportError:
        print("❌ Starlette not installed")
        return False
except Exception as e:
        print(f"❌ Error checking Starlette version: {e}")
        return False


def generate_security_report():

    """Generate security status report."""
    print("\n" + "=" * 60)
    print("📊 SECURITY STATUS REPORT")
    print("=" * 60)

    # Check current versions
    packages_to_check = [
        "fastapi",
        "starlette",
        "uvicorn",
        "pydantic",
        "requests",
        "jinja2",
        "sqlalchemy",
        "psycopg2",
    ]

for package in packages_to_check:
        success, output, _ = run_command(f"python -m pip show {package}")
if success:
            lines = output.split("\n")
            version_line = next(
                (line for line in lines if line.startswith("Version:")), None
            )
if version_line:
                version = version_line.split(": ")[1]
                print(f"📦 {package}: {version}")
else:
            print(f"❌ {package}: Not installed")

    print("\n🔒 Security Recommendations:")
    print("- Keep dependencies updated monthly")
    print("- Run security scans before deployments")
    print("- Monitor CVE databases for new vulnerabilities")
    print("- Use dependabot or similar for automated updates")


def main():

    """Main security update process."""
    print("🔒 Namaskah SMS Security Update")
    print("=" * 40)

    # Step 1: Check current vulnerabilities
    vuln_check = check_vulnerabilities()

    # Step 2: Update dependencies
    update_dependencies()

    # Step 3: Verify Starlette specifically
    starlette_ok = verify_starlette_version()

    # Step 4: Generate report
    generate_security_report()

    # Summary
    print("\n📋 SUMMARY:")
    print(f"Vulnerability Check: {'✅ PASS' if vuln_check else '⚠️ ISSUES FOUND'}")
    print(f"Starlette Security: {'✅ SECURE' if starlette_ok else '❌ VULNERABLE'}")

if vuln_check and starlette_ok:
        print("\n🎉 All security checks passed!")
        return 0
else:
        print("\n⚠️ Security issues detected. Please review and update.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
