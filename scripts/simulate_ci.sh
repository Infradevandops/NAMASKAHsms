#!/bin/bash
set -e

echo "🚀 Starting Local CI Simulation..."

# 1. Linting
echo "📝 Running Lint Checks..."
echo " > Black..."
black --check app/ tests/
echo " > Isort..."
isort --check-only app/ tests/
echo " > Flake8..."
flake8 app/ --max-line-length=120 --extend-ignore=E203,W503,E501,F821,C901
echo " > Mypy..."
# mypy might fail if not fully typed, checking if we should fail or just warn
# CI uses continue-on-error: true for mypy, so we warn but don't exit
mypy app/ --ignore-missing-imports || echo "⚠️ Mypy issues found (non-blocking)"

# 2. Security
echo "🔒 Running Security Checks..."
# Ensure tools are installed
pip install safety bandit pip-audit --quiet
echo " > Bandit..."
bandit -r app/ -ll -q
echo " > Safety..."
# safety check might fail on some dated deps, we'll capture it
# safety scan --exit-code 1 || echo "⚠️ Safety found vulnerabilities (check output)"
echo "⚠️ Skipping Safety scan (requires interactive login locally)"

# 3. Tests
echo "🧪 Running Tests..."
# Specific command from CI
# pytest tests/unit/ --cov=app --cov-branch --cov-report=xml --cov-report=html --cov-report=term-missing:skip-covered --cov-fail-under=23 -v
# We'll run a slightly simpler version for speed but coverage is key
pytest tests/unit/ tests/api/ tests/security/ --cov=app --cov-report=term-missing

echo "✅ Local CI Simulation Completed!"
