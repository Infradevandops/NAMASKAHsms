#!/bin/bash

# Phase 3: Test Execution Script
# Runs comprehensive tier identification system tests

set -e

echo "=========================================="
echo "Phase 3: Tier Identification System Tests"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test directories
BACKEND_TESTS="tests/unit/test_phase3_tier_identification.py"
INTEGRATION_TESTS="tests/integration/test_phase3_tier_identification.py"
FRONTEND_TESTS="tests/frontend/integration/tier-identification-e2e.test.js"

echo -e "${BLUE}1. Running Backend Unit Tests${NC}"
echo "   Testing 6 backend tier checks..."
python -m pytest "$BACKEND_TESTS" -v --tb=short --cov=app.middleware --cov=app.core.dependencies --cov=app.core.logging

echo ""
echo -e "${BLUE}2. Running Integration Tests${NC}"
echo "   Testing backend-frontend interaction..."
python -m pytest "$INTEGRATION_TESTS" -v --tb=short --cov=app.middleware --cov=app.services.tier_manager

echo ""
echo -e "${BLUE}3. Running Frontend Integration Tests${NC}"
echo "   Testing 6 frontend tier checks..."
npm test -- "$FRONTEND_TESTS" --coverage

echo ""
echo -e "${BLUE}4. Running All Tests with Coverage Report${NC}"
python -m pytest tests/unit/test_phase3_tier_identification.py tests/integration/test_phase3_tier_identification.py \
    -v \
    --cov=app \
    --cov-report=html \
    --cov-report=term-missing \
    --tb=short

echo ""
echo -e "${GREEN}✓ All Phase 3 tests completed${NC}"
echo ""
echo "Coverage Report:"
echo "  - Backend Unit Tests: 12 tier checks"
echo "  - Integration Tests: Backend-frontend interaction"
echo "  - Frontend Tests: UI consistency and synchronization"
echo ""
echo "HTML Coverage Report: htmlcov/index.html"
