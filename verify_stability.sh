#!/bin/bash
# Stability Verification Script
# Check all implementations for critical issues

set -e

echo "🔍 Namaskah Platform Stability Verification"
echo "==========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

ISSUES_FOUND=0

# 1. Check Python syntax
echo -e "${BLUE}1. Checking Python Syntax...${NC}"
if python3 -m py_compile app/**/*.py 2>/dev/null; then
    echo -e "${GREEN}✓ Python syntax valid${NC}"
else
    echo -e "${RED}✗ Python syntax errors found${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi
echo ""

# 2. Check for missing imports
echo -e "${BLUE}2. Checking for Missing Imports...${NC}"
if grep -r "from.*import" app/ | grep -v "__pycache__" > /dev/null; then
    echo -e "${GREEN}✓ Import statements found${NC}"
    
    # Check for common missing imports
    MISSING=0
    if ! grep -r "from fastapi import" app/middleware/*.py > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠ FastAPI imports may be missing in middleware${NC}"
        MISSING=1
    fi
    
    if [ $MISSING -eq 0 ]; then
        echo -e "${GREEN}✓ No obvious missing imports${NC}"
    fi
else
    echo -e "${YELLOW}⚠ No import statements found (unusual)${NC}"
fi
echo ""

# 3. Check database models
echo -e "${BLUE}3. Checking Database Models...${NC}"
if [ -d "app/models" ]; then
    MODEL_COUNT=$(find app/models -name "*.py" ! -name "__*" | wc -l)
    echo -e "${GREEN}✓ Found $MODEL_COUNT model files${NC}"
    
    # Check for critical models
    if [ -f "app/models/user.py" ]; then
        echo -e "${GREEN}✓ User model exists${NC}"
    else
        echo -e "${RED}✗ User model missing${NC}"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    fi
    
    if [ -f "app/models/transaction.py" ]; then
        echo -e "${GREEN}✓ Transaction model exists${NC}"
    else
        echo -e "${YELLOW}⚠ Transaction model missing${NC}"
    fi
else
    echo -e "${RED}✗ Models directory not found${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi
echo ""

# 4. Check services
echo -e "${BLUE}4. Checking Services...${NC}"
if [ -d "app/services" ]; then
    SERVICE_COUNT=$(find app/services -name "*.py" ! -name "__*" | wc -l)
    echo -e "${GREEN}✓ Found $SERVICE_COUNT service files${NC}"
    
    # Check critical services
    CRITICAL_SERVICES=("payment_service.py" "auth_service.py")
    for service in "${CRITICAL_SERVICES[@]}"; do
        if [ -f "app/services/$service" ]; then
            echo -e "${GREEN}✓ $service exists${NC}"
        else
            echo -e "${RED}✗ $service missing${NC}"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
        fi
    done
else
    echo -e "${RED}✗ Services directory not found${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi
echo ""

# 5. Check middleware
echo -e "${BLUE}5. Checking Middleware...${NC}"
if [ -d "app/middleware" ]; then
    if [ -f "app/middleware/rate_limiting.py" ]; then
        echo -e "${GREEN}✓ Rate limiting middleware exists${NC}"
    else
        echo -e "${YELLOW}⚠ Rate limiting middleware missing${NC}"
    fi
    
    if [ -f "app/middleware/security_headers.py" ]; then
        echo -e "${GREEN}✓ Security headers middleware exists${NC}"
    else
        echo -e "${YELLOW}⚠ Security headers middleware missing${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Middleware directory not found${NC}"
fi
echo ""

# 6. Check static files
echo -e "${BLUE}6. Checking Static Files...${NC}"
if [ -d "static/js" ]; then
    JS_COUNT=$(find static/js -name "*.js" | wc -l)
    echo -e "${GREEN}✓ Found $JS_COUNT JavaScript files${NC}"
    
    # Check for new features
    NEW_FEATURES=("verification-templates.js" "auto-copy-sms.js" "bulk-verification.js" "quick-retry.js")
    for feature in "${NEW_FEATURES[@]}"; do
        if [ -f "static/js/$feature" ]; then
            echo -e "${GREEN}✓ $feature exists${NC}"
        else
            echo -e "${YELLOW}⚠ $feature missing (Phase 3.4)${NC}"
        fi
    done
else
    echo -e "${RED}✗ Static JS directory not found${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi
echo ""

# 7. Check tests
echo -e "${BLUE}7. Checking Tests...${NC}"
if [ -d "tests/unit" ]; then
    TEST_COUNT=$(find tests/unit -name "test_*.py" | wc -l)
    echo -e "${GREEN}✓ Found $TEST_COUNT test files${NC}"
    
    # Check enhanced tests
    ENHANCED_TESTS=("test_payment_service_enhanced.py" "test_wallet_service_enhanced.py" "test_sms_service_enhanced.py" "test_auth_service_enhanced.py")
    for test in "${ENHANCED_TESTS[@]}"; do
        if [ -f "tests/unit/$test" ]; then
            echo -e "${GREEN}✓ $test exists${NC}"
        else
            echo -e "${YELLOW}⚠ $test missing (Phase 4.1)${NC}"
        fi
    done
else
    echo -e "${YELLOW}⚠ Tests directory not found${NC}"
fi
echo ""

# 8. Check configuration
echo -e "${BLUE}8. Checking Configuration...${NC}"
if [ -f ".env.example" ]; then
    echo -e "${GREEN}✓ .env.example exists${NC}"
else
    echo -e "${YELLOW}⚠ .env.example missing${NC}"
fi

if [ -f "requirements.txt" ]; then
    echo -e "${GREEN}✓ requirements.txt exists${NC}"
    REQ_COUNT=$(wc -l < requirements.txt)
    echo -e "${GREEN}  $REQ_COUNT dependencies${NC}"
else
    echo -e "${RED}✗ requirements.txt missing${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi

if [ -f "requirements-security.txt" ]; then
    echo -e "${GREEN}✓ requirements-security.txt exists${NC}"
else
    echo -e "${YELLOW}⚠ requirements-security.txt missing (Phase 4.3)${NC}"
fi
echo ""

# 9. Check main application
echo -e "${BLUE}9. Checking Main Application...${NC}"
if [ -f "main.py" ]; then
    echo -e "${GREEN}✓ main.py exists${NC}"
    
    # Check for FastAPI app
    if grep -q "FastAPI" main.py; then
        echo -e "${GREEN}✓ FastAPI app found${NC}"
    else
        echo -e "${RED}✗ FastAPI app not found in main.py${NC}"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    fi
else
    echo -e "${RED}✗ main.py missing${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi
echo ""

# 10. Check scripts
echo -e "${BLUE}10. Checking Scripts...${NC}"
SCRIPTS=("run_tests.sh" "security_scan.sh" "start.sh")
for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            echo -e "${GREEN}✓ $script exists and is executable${NC}"
        else
            echo -e "${YELLOW}⚠ $script exists but not executable${NC}"
            echo -e "${YELLOW}  Run: chmod +x $script${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ $script missing${NC}"
    fi
done
echo ""

# 11. Check documentation
echo -e "${BLUE}11. Checking Documentation...${NC}"
DOCS=("README.md" "TESTING_PLAN.md" "SECURITY_HARDENING_PLAN.md" "PHASE_4.1_IMPLEMENTATION.md" "PHASE_4.3_IMPLEMENTATION.md")
DOC_COUNT=0
for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        DOC_COUNT=$((DOC_COUNT + 1))
    fi
done
echo -e "${GREEN}✓ Found $DOC_COUNT/$((${#DOCS[@]})) documentation files${NC}"
echo ""

# 12. Critical issues check
echo -e "${BLUE}12. Checking for Critical Issues...${NC}"

# Check for TODO/FIXME
TODO_COUNT=$(grep -r "TODO\|FIXME" app/ 2>/dev/null | wc -l || echo 0)
if [ "$TODO_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠ Found $TODO_COUNT TODO/FIXME comments${NC}"
else
    echo -e "${GREEN}✓ No TODO/FIXME comments${NC}"
fi

# Check for print statements (should use logging)
PRINT_COUNT=$(grep -r "print(" app/ 2>/dev/null | grep -v "__pycache__" | wc -l || echo 0)
if [ "$PRINT_COUNT" -gt 5 ]; then
    echo -e "${YELLOW}⚠ Found $PRINT_COUNT print() statements (use logging)${NC}"
else
    echo -e "${GREEN}✓ Minimal print() usage${NC}"
fi

# Check for hardcoded secrets
if grep -r "password.*=.*['\"]" app/ 2>/dev/null | grep -v "__pycache__" | grep -v "test" > /dev/null; then
    echo -e "${RED}✗ Possible hardcoded passwords found${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
else
    echo -e "${GREEN}✓ No obvious hardcoded secrets${NC}"
fi
echo ""

# Summary
echo "==========================================="
echo -e "${BLUE}VERIFICATION SUMMARY${NC}"
echo "==========================================="
echo ""

if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED${NC}"
    echo -e "${GREEN}Platform is stable and ready for deployment${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Run tests: ./run_tests.sh"
    echo "2. Run security scan: ./security_scan.sh"
    echo "3. Deploy to production"
else
    echo -e "${RED}⚠️  FOUND $ISSUES_FOUND CRITICAL ISSUES${NC}"
    echo -e "${YELLOW}Review issues above and fix before deployment${NC}"
    echo ""
    echo "Priority fixes:"
    echo "1. Fix critical missing files"
    echo "2. Resolve syntax errors"
    echo "3. Add missing models/services"
    echo "4. Re-run verification"
fi
echo ""

exit $ISSUES_FOUND
