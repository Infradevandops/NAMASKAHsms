#!/bin/bash
# Test Runner Script
# Run all tests with coverage reporting

set -e

echo "🧪 Running Namaskah Test Suite"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest not found. Installing...${NC}"
    pip install pytest pytest-cov pytest-asyncio
fi

# Run tests with coverage
echo -e "${YELLOW}📊 Running tests with coverage...${NC}"
echo ""

pytest tests/unit/test_payment_service_enhanced.py \
       tests/unit/test_wallet_service_enhanced.py \
       tests/unit/test_sms_service_enhanced.py \
       tests/unit/test_auth_service_enhanced.py \
       --cov=app/services \
       --cov-report=term-missing \
       --cov-report=html \
       --cov-report=json \
       -v \
       --tb=short

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    
    # Display coverage summary
    echo "📈 Coverage Summary:"
    echo "==================="
    
    # Extract coverage percentage from JSON report
    if [ -f coverage.json ]; then
        python3 << EOF
import json
with open('coverage.json') as f:
    data = json.load(f)
    total = data['totals']['percent_covered']
    print(f"Total Coverage: {total:.2f}%")
    
    if total >= 50:
        print("✅ Coverage target met (50%+)")
    else:
        print(f"⚠️  Coverage below target: {total:.2f}% < 50%")
EOF
    fi
    
    echo ""
    echo "📁 HTML Report: htmlcov/index.html"
    echo ""
    
    # Open HTML report (macOS)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Opening coverage report..."
        open htmlcov/index.html
    fi
else
    echo ""
    echo -e "${RED}❌ Tests failed!${NC}"
    exit 1
fi
