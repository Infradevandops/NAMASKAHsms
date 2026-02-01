#!/usr/bin/env python3
"""Security validation script to check for common vulnerabilities."""

# Add project root to path

import re
import sys
from pathlib import Path
from typing import Any, Dict, List

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class SecurityChecker:

    """Security vulnerability checker."""

def __init__(self):

        self.issues = []
        self.project_root = project_root

def check_hardcoded_secrets(self) -> List[Dict[str, Any]]:

        """Check for hardcoded secrets in code."""
        issues = []
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded password"),
            (r'api_key\s*=\s*["\'][^"\']{20,}["\']', "Hardcoded API key"),
            (r'secret_key\s*=\s*["\'][^"\']{20,}["\']', "Hardcoded secret key"),
            (r'token\s*=\s*["\'][^"\']{20,}["\']', "Hardcoded token"),
        ]

for py_file in self.project_root.rglob("*.py"):
if "venv" in str(py_file) or "__pycache__" in str(py_file):
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
                                "severity": "HIGH",
                            }
                        )
except Exception:
                continue

        return issues

def check_sql_injection(self) -> List[Dict[str, Any]]:

        """Check for potential SQL injection vulnerabilities."""
        issues = []
        sql_patterns = [
            (r'execute\s*\(\s*["\'].*%.*["\']', "String formatting in SQL"),
            (r"execute\s*\(\s*.*\+.*\)", "String concatenation in SQL"),
            (r"query\s*=.*\+", "String concatenation in query"),
        ]

for py_file in self.project_root.rglob("*.py"):
if "venv" in str(py_file) or "__pycache__" in str(py_file):
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
                                "severity": "HIGH",
                            }
                        )
except Exception:
                continue

        return issues

def check_insecure_bindings(self) -> List[Dict[str, Any]]:

        """Check for insecure network bindings."""
        issues = []

        # Check configuration files
        config_files = [
            "app/core/config.py",
            "deploy.sh",
            "Dockerfile",
            "docker-compose.yml",
            "render.yaml",
        ]

for config_file in config_files:
            file_path = self.project_root / config_file
if not file_path.exists():
                continue

try:
                content = file_path.read_text()
if "0.0.0.0" in content and "HOST" not in content:
                    issues.append(
                        {
                            "file": config_file,
                            "line": 0,
                            "issue": "Hardcoded binding to 0.0.0.0",
                            "severity": "MEDIUM",
                        }
                    )
except Exception:
                continue

        return issues

def check_debug_mode(self) -> List[Dict[str, Any]]:

        """Check for debug mode enabled in production."""
        issues = []

        config_file = self.project_root / "app/core/config.py"
if config_file.exists():
try:
                content = config_file.read_text()
if re.search(r"debug\s*:\s*bool\s*=\s*True", content):
                    issues.append(
                        {
                            "file": "app/core/config.py",
                            "line": 0,
                            "issue": "Debug mode enabled by default",
                            "severity": "MEDIUM",
                        }
                    )
except Exception:
                pass

        return issues

def check_assert_statements(self) -> List[Dict[str, Any]]:

        """Check for assert statements in production code."""
        issues = []

for py_file in self.project_root.rglob("*.py"):
if "test" in str(py_file) or "venv" in str(py_file):
                continue

try:
                content = py_file.read_text()
                matches = re.finditer(r"\bassert\s+", content)
for match in matches:
                    line_num = content[: match.start()].count("\n") + 1
                    issues.append(
                        {
                            "file": str(py_file.relative_to(self.project_root)),
                            "line": line_num,
                            "issue": "Assert statement in production code",
                            "severity": "LOW",
                        }
                    )
except Exception:
                continue

        return issues

def check_subprocess_security(self) -> List[Dict[str, Any]]:

        """Check for insecure subprocess usage."""
        issues = []

for py_file in self.project_root.rglob("*.py"):
if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

try:
                content = py_file.read_text()

                # Check for shell=True
if "shell=True" in content:
                    line_num = content.find("shell=True")
                    line_num = content[:line_num].count("\n") + 1
                    issues.append(
                        {
                            "file": str(py_file.relative_to(self.project_root)),
                            "line": line_num,
                            "issue": "subprocess with shell=True",
                            "severity": "HIGH",
                        }
                    )

                # Check for direct command execution without path validation
                subprocess_patterns = [
                    r'subprocess\.run\s*\(\s*\[?\s*["\'][^"\']*["\']',
                    r'subprocess\.call\s*\(\s*["\'][^"\']*["\']',
                ]

for pattern in subprocess_patterns:
                    matches = re.finditer(pattern, content)
for match in matches:
if (
                            "shutil.which"
                            not in content[
                                max(0, match.start() - 200) : match.end() + 200
                            ]
                        ):
                            line_num = content[: match.start()].count("\n") + 1
                            issues.append(
                                {
                                    "file": str(py_file.relative_to(self.project_root)),
                                    "line": line_num,
                                    "issue": "subprocess without path validation",
                                    "severity": "MEDIUM",
                                }
                            )
except Exception:
                continue

        return issues

def run_all_checks(self) -> Dict[str, List[Dict[str, Any]]]:

        """Run all security checks."""
        return {
            "hardcoded_secrets": self.check_hardcoded_secrets(),
            "sql_injection": self.check_sql_injection(),
            "insecure_bindings": self.check_insecure_bindings(),
            "debug_mode": self.check_debug_mode(),
            "assert_statements": self.check_assert_statements(),
            "subprocess_security": self.check_subprocess_security(),
        }


def main():

    """Run security checks and report results."""
    print("🔒 Running security vulnerability checks...\n")

    checker = SecurityChecker()
    results = checker.run_all_checks()

    total_issues = 0
    severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

for check_name, issues in results.items():
if issues:
            print(f"🚨 {check_name.replace('_', ' ').title()}:")
for issue in issues:
                print(f"  📁 {issue['file']}:{issue['line']}")
                print(f"     {issue['issue']} [{issue['severity']}]")
                severity_counts[issue["severity"]] += 1
                total_issues += 1
            print()

    print("=" * 60)
    print("📊 SECURITY SUMMARY")
    print("=" * 60)
    print(f"Total Issues: {total_issues}")
    print(f"High Severity: {severity_counts['HIGH']}")
    print(f"Medium Severity: {severity_counts['MEDIUM']}")
    print(f"Low Severity: {severity_counts['LOW']}")

if total_issues == 0:
        print("\n✅ No security issues found!")
        return 0
elif severity_counts["HIGH"] > 0:
        print(f"\n❌ {severity_counts['HIGH']} high-severity issues found!")
        return 1
else:
        print(f"\n⚠️ {total_issues} issues found (no high-severity)")
        return 0


if __name__ == "__main__":
    sys.exit(main())