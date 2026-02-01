#!/usr/bin/env python3
"""Generate comprehensive analysis report from all security and quality checks."""


import json
import os
from datetime import datetime

class AnalysisReportGenerator:

def __init__(self):

        self.reports = {}
        self.summary = {
            "total_issues": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        }

def load_reports(self):

        """Load all analysis reports."""
        report_files = {
            "bandit": "bandit-report.json",
            "safety": "safety-report.json",
            "semgrep": "semgrep-report.json",
            "eslint": "eslint-security.json",
            "flake8": "flake8-report.json",
            "pylint": "pylint-report.json",
            "mypy": "mypy-report/index.json",
            "complexity": "complexity-report.json",
            "maintainability": "maintainability-report.json",
            "hadolint": "hadolint-report.json",
            "trivy_iac": "trivy-iac.json",
            "pip_audit": "pip-audit.json",
            "npm_audit": "npm-audit.json",
            "licenses": "licenses.json",
            "coverage": "coverage.json",
            "doc_coverage": "doc-coverage.txt",
            "pydocstyle": "pydocstyle-report.json",
            "api_security": "api-security-report.json",
            "trivy_container": "trivy-container.json",
            "grype": "grype-report.json",
            "gdpr": "gdpr-report.json",
            "pci": "pci-report.json",
            "owasp": "owasp-report.json",
        }

for name, filename in report_files.items():
if os.path.exists(filename):
try:
if filename.endswith(".json"):
with open(filename, "r") as f:
                            self.reports[name] = json.load(f)
else:
with open(filename, "r") as f:
                            self.reports[name] = f.read()
except Exception as e:
                    print(f"Error loading {filename}: {e}")

def analyze_security_issues(self):

        """Analyze security-related issues."""
        security_issues = []

        # Bandit issues
if "bandit" in self.reports:
for result in self.reports["bandit"].get("results", []):
                security_issues.append(
                    {
                        "tool": "bandit",
                        "severity": result.get("issue_severity", "MEDIUM"),
                        "confidence": result.get("issue_confidence", "MEDIUM"),
                        "file": result.get("filename", ""),
                        "line": result.get("line_number", 0),
                        "issue": result.get("issue_text", ""),
                        "test_id": result.get("test_id", ""),
                    }
                )

        # Semgrep issues
if "semgrep" in self.reports:
for result in self.reports["semgrep"].get("results", []):
                security_issues.append(
                    {
                        "tool": "semgrep",
                        "severity": result.get("extra", {}).get("severity", "MEDIUM"),
                        "file": result.get("path", ""),
                        "line": result.get("start", {}).get("line", 0),
                        "issue": result.get("extra", {}).get("message", ""),
                        "rule_id": result.get("check_id", ""),
                    }
                )

        return security_issues

def analyze_quality_issues(self):

        """Analyze code quality issues."""
        quality_issues = []

        # Flake8 issues
if "flake8" in self.reports:
for file_path, issues in self.reports["flake8"].items():
for issue in issues:
                    quality_issues.append(
                        {
                            "tool": "flake8",
                            "severity": "LOW",
                            "file": file_path,
                            "line": issue.get("line_number", 0),
                            "column": issue.get("column_number", 0),
                            "code": issue.get("code", ""),
                            "message": issue.get("text", ""),
                        }
                    )

        # Pylint issues
if "pylint" in self.reports:
for issue in self.reports["pylint"]:
                severity_map = {"error": "HIGH", "warning": "MEDIUM", "info": "LOW"}
                quality_issues.append(
                    {
                        "tool": "pylint",
                        "severity": severity_map.get(issue.get("type", "info"), "LOW"),
                        "file": issue.get("path", ""),
                        "line": issue.get("line", 0),
                        "column": issue.get("column", 0),
                        "symbol": issue.get("symbol", ""),
                        "message": issue.get("message", ""),
                    }
                )

        return quality_issues

def analyze_dependencies(self):

        """Analyze dependency vulnerabilities."""
        dependency_issues = []

        # Safety issues
if "safety" in self.reports:
for vuln in self.reports["safety"]:
                dependency_issues.append(
                    {
                        "tool": "safety",
                        "severity": "HIGH",
                        "package": vuln.get("package_name", ""),
                        "version": vuln.get("installed_version", ""),
                        "vulnerability": vuln.get("vulnerability_id", ""),
                        "advisory": vuln.get("advisory", ""),
                    }
                )

        # NPM Audit issues
if "npm_audit" in self.reports:
            advisories = self.reports["npm_audit"].get("advisories", {})
for advisory_id, advisory in advisories.items():
                severity_map = {
                    "critical": "CRITICAL",
                    "high": "HIGH",
                    "moderate": "MEDIUM",
                    "low": "LOW",
                }
                dependency_issues.append(
                    {
                        "tool": "npm_audit",
                        "severity": severity_map.get(
                            advisory.get("severity", "medium"), "MEDIUM"
                        ),
                        "package": advisory.get("module_name", ""),
                        "title": advisory.get("title", ""),
                        "overview": advisory.get("overview", ""),
                        "cves": advisory.get("cves", []),
                    }
                )

        return dependency_issues

def calculate_summary(self, all_issues):

        """Calculate summary statistics."""
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}

for issue in all_issues:
            severity = issue.get("severity", "LOW").upper()
if severity in severity_counts:
                severity_counts[severity] += 1

        self.summary = {
            "total_issues": len(all_issues),
            "critical": severity_counts["CRITICAL"],
            "high": severity_counts["HIGH"],
            "medium": severity_counts["MEDIUM"],
            "low": severity_counts["LOW"],
            "info": severity_counts["INFO"],
        }

def generate_html_report(self, all_issues):

        """Generate HTML report."""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Comprehensive Code Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .metric {{ background: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 5px; text-align: center; }}
        .critical {{ border-left: 5px solid #d32f2f; }}
        .high {{ border-left: 5px solid #f57c00; }}
        .medium {{ border-left: 5px solid #fbc02d; }}
        .low {{ border-left: 5px solid #388e3c; }}
        .issue {{ margin: 10px 0; padding: 10px; border-left: 3px solid #ccc; background: #f9f9f9; }}
        .tool-section {{ margin: 20px 0; }}
        .tool-header {{ background: #e3f2fd; padding: 10px; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Comprehensive Code Analysis Report</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Total Issues Found: {self.summary['total_issues']}</p>
    </div>

    <div class="summary">
        <div class="metric critical">
            <h3>{self.summary['critical']}</h3>
            <p>Critical</p>
        </div>
        <div class="metric high">
            <h3>{self.summary['high']}</h3>
            <p>High</p>
        </div>
        <div class="metric medium">
            <h3>{self.summary['medium']}</h3>
            <p>Medium</p>
        </div>
        <div class="metric low">
            <h3>{self.summary['low']}</h3>
            <p>Low</p>
        </div>
    </div>

    <div class="issues">
        <h2>Issues by Tool</h2>
"""

        # Group issues by tool
        issues_by_tool = {}
for issue in all_issues:
            tool = issue.get("tool", "unknown")
if tool not in issues_by_tool:
                issues_by_tool[tool] = []
            issues_by_tool[tool].append(issue)

for tool, issues in issues_by_tool.items():
            html_template += """
        <div class="tool-section">
            <div class="tool-header">{tool.upper()} ({len(issues)} issues)</div>
"""
for issue in issues[:10]:  # Limit to first 10 issues per tool
                issue.get("severity", "low").lower()
                html_template += """
            <div class="issue {severity_class}">
                <strong>{issue.get('severity', 'LOW')}</strong> -
                {issue.get('file', 'N/A')}:{issue.get('line', 'N/A')} -
                {issue.get('message', issue.get('issue', 'No description'))}
            </div>
"""
if len(issues) > 10:
                html_template += (
                    f"<p><em>... and {len(issues) - 10} more issues</em></p>"
                )
            html_template += "</div>"

        html_template += """
    </div>
</body>
</html>
"""

with open("analysis-report.html", "w") as f:
            f.write(html_template)

def generate_json_report(self, all_issues):

        """Generate JSON report."""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.summary,
            "issues": all_issues,
            "raw_reports": self.reports,
        }

with open("analysis-report.json", "w") as f:
            json.dump(report_data, f, indent=2)

def generate_reports(self):

        """Generate comprehensive analysis reports."""
        print("Loading analysis reports...")
        self.load_reports()

        print("Analyzing security issues...")
        security_issues = self.analyze_security_issues()

        print("Analyzing quality issues...")
        quality_issues = self.analyze_quality_issues()

        print("Analyzing dependency issues...")
        dependency_issues = self.analyze_dependencies()

        all_issues = security_issues + quality_issues + dependency_issues

        print("Calculating summary...")
        self.calculate_summary(all_issues)

        print("Generating HTML report...")
        self.generate_html_report(all_issues)

        print("Generating JSON report...")
        self.generate_json_report(all_issues)

        print(
            """
Analysis Complete!
==================
Total Issues: {self.summary['total_issues']}
Critical: {self.summary['critical']}
High: {self.summary['high']}
Medium: {self.summary['medium']}
Low: {self.summary['low']}

Reports generated:
- analysis-report.html
- analysis-report.json
"""
        )


if __name__ == "__main__":
    generator = AnalysisReportGenerator()
    generator.generate_reports()