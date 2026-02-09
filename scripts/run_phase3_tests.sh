#!/bin/bash
# Phase 3 Test Runner Script

echo "🧪 PHASE 3: TESTING & QA"
echo "========================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run test and track result
run_test() {
    local test_name=$1
    local test_command=$2
    
    echo -e "${YELLOW}Running: $test_name${NC}"
    if eval $test_command; then
        echo -e "${GREEN}✅ $test_name PASSED${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ $test_name FAILED${NC}"
        ((TESTS_FAILED++))
    fi
    echo ""
}

# 1. Unit Tests with Coverage
echo "📊 1. UNIT TESTS WITH COVERAGE"
echo "--------------------------------"
run_test "Unit Tests" "pytest tests/unit/ --cov=app --cov-report=term-missing --cov-report=html -v"

# 2. Integration Tests
echo "🔗 2. INTEGRATION TESTS"
echo "--------------------------------"
run_test "Integration Tests" "pytest tests/integration/ -v"

# 3. E2E Tests (if Playwright installed)
if command -v playwright &> /dev/null; then
    echo "🎭 3. E2E TESTS"
    echo "--------------------------------"
    run_test "E2E Tests" "pytest tests/e2e/ -v"
else
    echo "⚠️  Playwright not installed. Skipping E2E tests."
    echo "   Install with: pip install playwright && playwright install"
fi

# 4. Security Audit
echo "🔒 4. SECURITY AUDIT"
echo "--------------------------------"
run_test "Security Audit" "python scripts/security_audit.py"

# 5. Performance Tests (optional - requires running server)
echo "⚡ 5. PERFORMANCE TESTS"
echo "--------------------------------"
echo "ℹ️  Performance tests require manual execution:"
echo "   locust -f tests/load/locustfile.py --host=http://localhost:8000"
echo ""

# Summary
echo "================================"
echo "📊 TEST SUMMARY"
echo "================================"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Review output above.${NC}"
    exit 1
fi
