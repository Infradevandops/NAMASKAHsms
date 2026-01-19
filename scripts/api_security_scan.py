#!/usr/bin/env python3
"""API Security Scanner for FastAPI endpoints."""
import json
import re
from pathlib import Path


class APISecurityScanner:
    def __init__(self):
        self.issues = []
        self.project_root = Path(__file__).parent.parent

    def scan_endpoints(self):
        """Scan API endpoints for security issues."""
        api_files = list((self.project_root / "app" / "api").glob("*.py"))

        for api_file in api_files:
            self.scan_file(api_file)

    def scan_file(self, file_path: Path):
        """Scan individual API file."""
        try:
            content = file_path.read_text()

            # Check for missing authentication
            self.check_missing_auth(content, file_path)

            # Check for SQL injection risks
            self.check_sql_injection(content, file_path)

            # Check for input validation
            self.check_input_validation(content, file_path)

            # Check for rate limiting
            self.check_rate_limiting(content, file_path)

            # Check for CORS configuration
            self.check_cors_config(content, file_path)

        except Exception as e:
            self.add_issue(file_path, 0, f"Error scanning file: {e}", "LOW")

    def check_missing_auth(self, content: str, file_path: Path):
        """Check for endpoints without authentication."""
        # Find all route definitions
        route_pattern = r"@router\.(get|post|put|delete|patch)\s*\([^)]*\)"
        routes = re.finditer(route_pattern, content, re.IGNORECASE)

        for route in routes:
            route_text = route.group(0)
            line_num = content[: route.start()].count("\n") + 1

            # Check if Depends(get_current_user) or similar auth is present
            if (
                "Depends(" not in route_text
                and "get_current_user" not in content[route.end() : route.end() + 200]
            ):
                self.add_issue(
                    file_path, line_num, "Endpoint missing authentication", "HIGH"
                )

    def check_sql_injection(self, content: str, file_path: Path):
        """Check for SQL injection vulnerabilities."""
        sql_patterns = [
            r'execute\s*\(\s*f["\'].*\{.*\}.*["\']',  # f-string in execute
            r'execute\s*\(\s*["\'].*%.*["\']',  # % formatting in execute
            r"query\s*=.*\+",  # String concatenation
        ]

        for pattern in sql_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[: match.start()].count("\n") + 1
                self.add_issue(
                    file_path,
                    line_num,
                    "Potential SQL injection vulnerability",
                    "CRITICAL",
                )

    def check_input_validation(self, content: str, file_path: Path):
        """Check for missing input validation."""
        # Check for endpoints that don't use Pydantic models
        endpoint_pattern = r"async def \w+\([^)]*\):"
        endpoints = re.finditer(endpoint_pattern, content)

        for endpoint in endpoints:
            endpoint_text = endpoint.group(0)
            line_num = content[: endpoint.start()].count("\n") + 1

            # Check if parameters are validated
            if ":" not in endpoint_text or "str" in endpoint_text:
                # Look for validation in the next 5 lines
                next_lines = content[endpoint.end() : endpoint.end() + 500]
                if (
                    "validate" not in next_lines.lower()
                    and "pydantic" not in next_lines.lower()
                ):
                    self.add_issue(
                        file_path, line_num, "Missing input validation", "MEDIUM"
                    )

    def check_rate_limiting(self, content: str, file_path: Path):
        """Check for missing rate limiting."""
        if "@limiter.limit" not in content and "RateLimiter" not in content:
            self.add_issue(
                file_path, 1, "Missing rate limiting configuration", "MEDIUM"
            )

    def check_cors_config(self, content: str, file_path: Path):
        """Check for insecure CORS configuration."""
        cors_patterns = [
            r'allow_origins\s*=\s*\[\s*["\']?\*["\']?\s*\]',  # Allow all origins
            r"allow_credentials\s*=\s*True.*allow_origins.*\*",  # Credentials with wildcard
        ]

        for pattern in cors_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[: match.start()].count("\n") + 1
                self.add_issue(
                    file_path, line_num, "Insecure CORS configuration", "HIGH"
                )

    def add_issue(self, file_path: Path, line: int, message: str, severity: str):
        """Add security issue to the list."""
        self.issues.append(
            {
                "file": str(file_path.relative_to(self.project_root)),
                "line": line,
                "message": message,
                "severity": severity,
                "tool": "api_security_scanner",
            }
        )

    def generate_report(self):
        """Generate security report."""
        return {
            "timestamp": "2024-01-01T00:00:00Z",
            "total_issues": len(self.issues),
            "issues": self.issues,
            "summary": {
                "critical": len(
                    [i for i in self.issues if i["severity"] == "CRITICAL"]
                ),
                "high": len([i for i in self.issues if i["severity"] == "HIGH"]),
                "medium": len([i for i in self.issues if i["severity"] == "MEDIUM"]),
                "low": len([i for i in self.issues if i["severity"] == "LOW"]),
            },
        }


def main():
    scanner = APISecurityScanner()
    scanner.scan_endpoints()
    report = scanner.generate_report()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
