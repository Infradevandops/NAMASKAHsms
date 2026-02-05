#!/usr/bin/env python3
"""Automated security scanning script."""


import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

class SecurityScanner:

    """Automated security scanner for the application."""

    def __init__(self, project_root: str):

        self.project_root = Path(project_root)
        self.issues = []

    def scan_all(self) -> Dict:

        """Run all security scans."""
        print("🔍 Starting comprehensive security scan...")

        results = {
            "hardcoded_secrets": self.scan_hardcoded_secrets(),
            "sql_injection": self.scan_sql_injection(),
            "xss_vulnerabilities": self.scan_xss_vulnerabilities(),
            "log_injection": self.scan_log_injection(),
            "insecure_functions": self.scan_insecure_functions(),
            "dependency_vulnerabilities": self.scan_dependencies(),
            "file_permissions": self.check_file_permissions(),
            "configuration_issues": self.scan_configuration(),
        }

        total_issues = sum(len(issues) for issues in results.values())

        print("\n📊 Security Scan Results:")
        print(f"Total issues found: {total_issues}")

        for category, issues in results.items():
        if issues:
                print(f"  {category}: {len(issues)} issues")

        return results

    def scan_hardcoded_secrets(self) -> List[Dict]:

        """Scan for hardcoded secrets and credentials."""
        print("🔐 Scanning for hardcoded secrets...")

        issues = []
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']{6,}["\']', "Hardcoded password"),
            (r'api_key\s*=\s*["\'][^"\']{10,}["\']', "Hardcoded API key"),
            (r'secret_key\s*=\s*["\'][^"\']{10,}["\']', "Hardcoded secret key"),
            (r'token\s*=\s*["\'][^"\']{10,}["\']', "Hardcoded token"),
            (r"sk_test_[a-zA-Z0-9]{24,}", "Stripe test key"),
            (r"sk_live_[a-zA-Z0-9]{24,}", "Stripe live key"),
            (r"AKIA[0-9A-Z]{16}", "AWS access key"),
        ]

        for py_file in self.project_root.rglob("*.py"):
        if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue

        try:
                content = py_file.read_text()
        for pattern, description in secret_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
                        line_num = content[: match.start()].count("\n") + 1
                        issues.append(
                            {
                                "file": str(py_file.relative_to(self.project_root)),
                                "line": line_num,
                                "issue": description,
                                "code": match.group(0)[:50] + "...",
                            }
                        )
        except Exception as e:
                print(f"Error scanning {py_file}: {e}")

        return issues

    def scan_sql_injection(self) -> List[Dict]:

        """Scan for SQL injection vulnerabilities."""
        print("💉 Scanning for SQL injection vulnerabilities...")

        issues = []
        sql_patterns = [
            (r'f".*SELECT.*{.*}"', "F-string in SQL query"),
            (r"f\'.*SELECT.*{.*}\'", "F-string in SQL query"),
            (r'".*SELECT.*"\s*\+', "String concatenation in SQL"),
            (r"\'.*SELECT.*\'\s*\+", "String concatenation in SQL"),
            (r"\.format\(.*\).*SELECT", "String format in SQL"),
            (r"%.*SELECT.*%", "String formatting in SQL"),
        ]

        for py_file in self.project_root.rglob("*.py"):
        if "__pycache__" in str(py_file):
                continue

        try:
                content = py_file.read_text()
        for pattern, description in sql_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
                        line_num = content[: match.start()].count("\n") + 1
                        issues.append(
                            {
                                "file": str(py_file.relative_to(self.project_root)),
                                "line": line_num,
                                "issue": description,
                                "code": match.group(0)[:100] + "...",
                            }
                        )
        except Exception as e:
                print(f"Error scanning {py_file}: {e}")

        return issues

    def scan_xss_vulnerabilities(self) -> List[Dict]:

        """Scan for XSS vulnerabilities."""
        print("🕷️ Scanning for XSS vulnerabilities...")

        issues = []
        xss_patterns = [
            (r"return.*{.*user_input.*}", "Unescaped user input in response"),
            (r'f".*{.*user.*}.*"', "User data in f-string"),
            (r"\.format\(.*user.*\)", "User data in string format"),
            (r"innerHTML.*=.*user", "Direct innerHTML assignment"),
        ]

        for py_file in self.project_root.rglob("*.py"):
        if "__pycache__" in str(py_file):
                continue

        try:
                content = py_file.read_text()
        for pattern, description in xss_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
                        line_num = content[: match.start()].count("\n") + 1
                        issues.append(
                            {
                                "file": str(py_file.relative_to(self.project_root)),
                                "line": line_num,
                                "issue": description,
                                "code": match.group(0)[:100] + "...",
                            }
                        )
        except Exception as e:
                print(f"Error scanning {py_file}: {e}")

        return issues

    def scan_log_injection(self) -> List[Dict]:

        """Scan for log injection vulnerabilities."""
        print("📝 Scanning for log injection vulnerabilities...")

        issues = []
        log_patterns = [
            (r'logger\.\w+\(f".*{.*}"', "F-string in logger"),
            (r"logger\.\w+\(.*\+.*\)", "String concatenation in logger"),
            (r'print\(f".*{.*user.*}"', "User data in print statement"),
        ]

        for py_file in self.project_root.rglob("*.py"):
        if "__pycache__" in str(py_file):
                continue

        try:
                content = py_file.read_text()
        for pattern, description in log_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
                        line_num = content[: match.start()].count("\n") + 1
                        issues.append(
                            {
                                "file": str(py_file.relative_to(self.project_root)),
                                "line": line_num,
                                "issue": description,
                                "code": match.group(0)[:100] + "...",
                            }
                        )
        except Exception as e:
                print(f"Error scanning {py_file}: {e}")

        return issues

    def scan_insecure_functions(self) -> List[Dict]:

        """Scan for insecure function usage."""
        print("⚠️ Scanning for insecure functions...")

        issues = []
        insecure_patterns = [
            (r"eval\s*\(", "Use of eval() function"),
            (r"exec\s*\(", "Use of exec() function"),
            (r"os\.system\s*\(", "Use of os.system()"),
            (r"subprocess\.call\s*\(.*shell=True", "Shell injection risk"),
            (r"pickle\.loads?\s*\(", "Insecure pickle usage"),
            (r"yaml\.load\s*\(", "Unsafe YAML loading"),
            (r"random\.random\s*\(", "Weak random number generation"),
        ]

        for py_file in self.project_root.rglob("*.py"):
        if "__pycache__" in str(py_file):
                continue

        try:
                content = py_file.read_text()
        for pattern, description in insecure_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
                        line_num = content[: match.start()].count("\n") + 1
                        issues.append(
                            {
                                "file": str(py_file.relative_to(self.project_root)),
                                "line": line_num,
                                "issue": description,
                                "code": match.group(0)[:100] + "...",
                            }
                        )
        except Exception as e:
                print(f"Error scanning {py_file}: {e}")

        return issues

    def scan_dependencies(self) -> List[Dict]:

        """Scan for vulnerable dependencies."""
        print("📦 Scanning dependencies for vulnerabilities...")

        issues = []
        requirements_file = self.project_root / "requirements.txt"

        if requirements_file.exists():
        try:
                # Try to run safety check if available
                result = subprocess.run(
                    ["safety", "check", "-r", str(requirements_file)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

        if (
                    result.returncode != 0
                    and "No known security vulnerabilities found" not in result.stdout
                ):
                    issues.append(
                        {
                            "file": "requirements.txt",
                            "line": 0,
                            "issue": "Vulnerable dependencies found",
                            "code": result.stdout[:200] + "...",
                        }
                    )
        except (subprocess.TimeoutExpired, FileNotFoundError):
                # Safety not installed or timeout
                issues.append(
                    {
                        "file": "requirements.txt",
                        "line": 0,
                        "issue": "Could not check dependencies (install 'safety' package)",
                        "code": "pip install safety",
                    }
                )

        return issues

    def check_file_permissions(self) -> List[Dict]:

        """Check for insecure file permissions."""
        print("🔒 Checking file permissions...")

        issues = []

        # Check for world-writable files
        for file_path in self.project_root.rglob("*"):
        if file_path.is_file():
        try:
                    stat = file_path.stat()
                    # Check if world-writable (others have write permission)
        if stat.st_mode & 0o002:
                        issues.append(
                            {
                                "file": str(file_path.relative_to(self.project_root)),
                                "line": 0,
                                "issue": "World-writable file",
                                "code": f"chmod o-w {file_path}",
                            }
                        )
        except Exception:
                    pass

        return issues

    def scan_configuration(self) -> List[Dict]:

        """Scan configuration files for security issues."""
        print("⚙️ Scanning configuration files...")

        issues = []

        # Check .env files
        for env_file in self.project_root.rglob(".env*"):
        if env_file.is_file():
        try:
                    content = env_file.read_text()

                    # Check for debug mode in production
        if "DEBUG=True" in content or "DEBUG=true" in content:
                        issues.append(
                            {
                                "file": str(env_file.relative_to(self.project_root)),
                                "line": 0,
                                "issue": "Debug mode enabled",
                                "code": "DEBUG=True",
                            }
                        )

                    # Check for weak secrets
        if "SECRET_KEY=test" in content or "SECRET_KEY=dev" in content:
                        issues.append(
                            {
                                "file": str(env_file.relative_to(self.project_root)),
                                "line": 0,
                                "issue": "Weak secret key",
                                "code": "SECRET_KEY=test",
                            }
                        )

        except Exception as e:
                    print(f"Error reading {env_file}: {e}")

        return issues

    def generate_report(self, results: Dict) -> str:

        """Generate security scan report."""
        report = ["# Security Scan Report\n"]

        total_issues = sum(len(issues) for issues in results.values())

        if total_issues == 0:
            report.append("✅ **No security issues found!**\n")
        else:
            report.append(f"⚠️ **{total_issues} security issues found**\n")

        for category, issues in results.items():
        if issues:
                report.append(f"\n## {category.replace('_', ' ').title()}\n")

        for issue in issues:
                    report.append(
                        f"- **{issue['file']}:{issue['line']}** - {issue['issue']}"
                    )
                    report.append(f"  ```\n  {issue['code']}\n  ```\n")

        return "\n".join(report)


    def main():

        """Main function."""
        if len(sys.argv) > 1:
        project_root = sys.argv[1]
        else:
        project_root = os.getcwd()

        scanner = SecurityScanner(project_root)
        results = scanner.scan_all()

    # Generate report
        report = scanner.generate_report(results)

    # Save report
        report_file = Path(project_root) / "security_scan_report.md"
        report_file.write_text(report)

        print(f"\n📄 Report saved to: {report_file}")

    # Exit with error code if issues found
        total_issues = sum(len(issues) for issues in results.values())
        sys.exit(1 if total_issues > 0 else 0)


        if __name__ == "__main__":
        main()
