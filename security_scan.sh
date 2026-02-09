#!/bin/bash
# Security Scanning Script
# Run automated security scans

set -e

echo "🔒 Running Security Scans"
echo "========================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Create reports directory
mkdir -p security_reports

# 1. Bandit - Python security linter
echo -e "${YELLOW}1. Running Bandit (Python Security)...${NC}"
if command -v bandit &> /dev/null; then
    bandit -r app/ -f json -o security_reports/bandit_report.json || true
    bandit -r app/ -f txt
    echo -e "${GREEN}✓ Bandit scan complete${NC}"
else
    echo -e "${RED}✗ Bandit not installed. Run: pip install bandit${NC}"
fi
echo ""

# 2. Safety - Dependency vulnerability scanner
echo -e "${YELLOW}2. Running Safety (Dependency Check)...${NC}"
if command -v safety &> /dev/null; then
    safety check --json > security_reports/safety_report.json || true
    safety check
    echo -e "${GREEN}✓ Safety scan complete${NC}"
else
    echo -e "${RED}✗ Safety not installed. Run: pip install safety${NC}"
fi
echo ""

# 3. pip-audit - PyPI package auditor
echo -e "${YELLOW}3. Running pip-audit...${NC}"
if command -v pip-audit &> /dev/null; then
    pip-audit --format json > security_reports/pip_audit_report.json || true
    pip-audit
    echo -e "${GREEN}✓ pip-audit scan complete${NC}"
else
    echo -e "${RED}✗ pip-audit not installed. Run: pip install pip-audit${NC}"
fi
echo ""

# 4. Semgrep - Static analysis
echo -e "${YELLOW}4. Running Semgrep (Static Analysis)...${NC}"
if command -v semgrep &> /dev/null; then
    semgrep --config=auto app/ --json > security_reports/semgrep_report.json || true
    semgrep --config=auto app/
    echo -e "${GREEN}✓ Semgrep scan complete${NC}"
else
    echo -e "${YELLOW}⚠ Semgrep not installed. Run: pip install semgrep${NC}"
fi
echo ""

# 5. Check for secrets
echo -e "${YELLOW}5. Checking for secrets...${NC}"
if command -v trufflehog &> /dev/null; then
    trufflehog filesystem . --json > security_reports/secrets_report.json || true
    echo -e "${GREEN}✓ Secrets scan complete${NC}"
else
    echo -e "${YELLOW}⚠ TruffleHog not installed${NC}"
fi
echo ""

# 6. Check requirements.txt for known vulnerabilities
echo -e "${YELLOW}6. Checking requirements.txt...${NC}"
if [ -f requirements.txt ]; then
    echo "Checking for outdated packages..."
    pip list --outdated
    echo -e "${GREEN}✓ Requirements check complete${NC}"
fi
echo ""

# Summary
echo "================================"
echo -e "${GREEN}Security Scans Complete!${NC}"
echo ""
echo "📁 Reports saved to: security_reports/"
echo ""
echo "Next steps:"
echo "1. Review reports in security_reports/"
echo "2. Fix critical and high severity issues"
echo "3. Update dependencies: pip install -U -r requirements.txt"
echo "4. Re-run scans to verify fixes"
echo ""

# Check for critical issues
if [ -f security_reports/bandit_report.json ]; then
    CRITICAL=$(grep -o '"issue_severity": "HIGH"' security_reports/bandit_report.json | wc -l)
    if [ "$CRITICAL" -gt 0 ]; then
        echo -e "${RED}⚠️  Found $CRITICAL high severity issues!${NC}"
        echo "Review: security_reports/bandit_report.json"
    else
        echo -e "${GREEN}✅ No high severity issues found${NC}"
    fi
fi
