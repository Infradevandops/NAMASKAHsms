#!/bin/bash
# Run CI checks locally before pushing
# This script mirrors the GitHub Actions CI pipeline

set -e

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                     Running CI Checks Locally                                ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILURES=0

# Function to run a check
run_check() {
    local name=$1
    local command=$2
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📝 Running: $name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if eval "$command"; then
        echo -e "${GREEN}✅ $name passed${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}❌ $name failed${NC}"
        echo ""
        FAILURES=$((FAILURES + 1))
        return 1
    fi
}

# 1. Code Formatting
run_check "Black (code formatting)" \
    "black --check app/ tests/ --line-length=120"

run_check "isort (import sorting)" \
    "isort --check-only app/ tests/ --line-length=120"

# 2. Linting
run_check "Flake8 (linting)" \
    "flake8 app/ tests/ --max-line-length=120 --extend-ignore=E203,W503,E501,F821,C901"

# 3. Type Checking
run_check "Mypy (type checking)" \
    "mypy app/ --ignore-missing-imports"

# 4. Unit Tests
run_check "Unit Tests with Coverage" \
    "pytest tests/unit/ -v --cov=app --cov-fail-under=40 --cov-report=term-missing:skip-covered"

# 5. Security Checks
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔒 Running: Security Checks"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "  → Bandit (security issues)"
if bandit -r app/ -ll; then
    echo -e "${GREEN}✅ Bandit passed${NC}"
else
    echo -e "${RED}❌ Bandit found security issues${NC}"
    FAILURES=$((FAILURES + 1))
fi

echo ""
echo "  → Safety (dependency vulnerabilities)"
if safety check -r requirements.txt --exit-code 1 2>/dev/null; then
    echo -e "${GREEN}✅ Safety passed${NC}"
else
    echo -e "${YELLOW}⚠️  Safety found vulnerabilities (may need updates)${NC}"
fi

echo ""

# Summary
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                              Summary                                         ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Ready to push.${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}❌ $FAILURES check(s) failed. Please fix before pushing.${NC}"
    echo ""
    echo "Quick fixes:"
    echo "  • Format code: black app/ tests/ && isort app/ tests/"
    echo "  • Run tests: pytest tests/unit/ -v"
    echo "  • Check security: bandit -r app/ -ll"
    echo ""
    exit 1
fi
