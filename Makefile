# Namaskah SMS Analytics - Development Makefile

.PHONY: install lint format test security-check build clean help \
	fix-all fix-db fix-middleware fix-broken-files fix-pricing-router \
	fix-commented-code fix-migrations fix-env \
	test-integration test-coverage-report test-coverage-50 \
	health-check health-external audit-env pre-commit-setup

# Default target
help:
	@echo ""
	@echo "=== CRITICAL FIXES ==="
	@echo "  fix-all            - Run all automated fix checks"
	@echo "  fix-db             - Verify database connection"
	@echo "  fix-middleware     - Check & report middleware status"
	@echo "  fix-broken-files   - Find and remove .broken files"
	@echo "  fix-pricing-router - Verify pricing router can be re-enabled"
	@echo "  fix-commented-code - List all 'Temporarily disabled' comments"
	@echo "  fix-migrations     - Audit migration idempotency"
	@echo "  fix-env            - Validate required environment variables"
	@echo ""
	@echo "=== TESTING ==="
	@echo "  test-integration   - Run integration tests (requires Docker)"
	@echo "  test-coverage-report - Generate HTML coverage report"
	@echo "  test-coverage-50   - Run coverage and fail if below 50%"
	@echo ""
	@echo "=== MONITORING ==="
	@echo "  health-check       - Check app health endpoint"
	@echo "  health-external    - Check external services health"
	@echo ""
	@echo "=== STANDARD ==="
	@echo "  install        - Install dependencies"
	@echo "  lint           - Run linters"
	@echo "  lint-fix       - Run linters with auto-fix"
	@echo "  format         - Format code"
	@echo "  test           - Run tests"
	@echo "  test-watch     - Run tests in watch mode"
	@echo "  test-coverage  - Run tests with coverage"
	@echo "  security-check - Run security checks"
	@echo "  build          - Build and validate everything"
	@echo "  clean          - Clean build artifacts"
	@echo "  pre-commit-setup - Install pre-commit hooks"
	@echo ""

# Install dependencies
install:
	pip install -r requirements.txt
	pip install -r requirements/requirements-test.txt

# Linting
lint:
	npm run lint
	flake8 app/ --max-line-length=88 --extend-ignore=E203,W503
	mypy app/ --ignore-missing-imports

lint-fix:
	npm run lint:fix
	black app/
	isort app/

# Formatting
format:
	npm run format
	black app/
	isort app/

# Testing
test:
	pytest tests/ -v --cov=app --cov-report=html

test-watch:
	npm run test:watch

test-coverage:
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term

# Security
security-check:
	npm audit
	npm run security-check
	bandit -r app/ -f json -o security-report.json || true
	safety check

# Build pipeline
build: lint format test security-check
	@echo "✅ Build completed successfully"

# Clean up
clean:
	rm -rf node_modules/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -f security-report.json
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Development server
dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production checks
prod-check:
	@echo "Running production readiness checks..."
	pytest tests/ -v
	bandit -r app/ -ll
	@echo "✅ Production checks passed"

# =============================================================
# CRITICAL FIXES
# =============================================================

## Run all fix checks in sequence
fix-all: fix-db fix-broken-files fix-middleware fix-commented-code fix-env
	@echo ""
	@echo "✅ All fix checks complete — review output above"

## T1: Verify database connection
fix-db:
	@echo "--- T1: Database Connection ---"
	@python -c "\
from app.core.database import test_database_connection; \
result = test_database_connection(); \
print('✅ DB OK:', result) if result.get('status') == 'connected' else print('❌ DB FAIL:', result)\
" 2>&1 || echo "❌ Could not import database module"

## T2+T3: Check middleware imports and report disabled middleware
fix-middleware:
	@echo "--- T2: Security Middleware Status ---"
	@python -m py_compile app/middleware/csrf_middleware.py 2>/dev/null \
		&& echo "✅ csrf_middleware: OK" || echo "❌ csrf_middleware: SYNTAX ERROR"
	@python -m py_compile app/middleware/security.py 2>/dev/null \
		&& echo "✅ security: OK" || echo "❌ security: SYNTAX ERROR"
	@python -m py_compile app/middleware/xss_protection.py 2>/dev/null \
		&& echo "✅ xss_protection: OK" || echo "❌ xss_protection: SYNTAX ERROR"
	@python -m py_compile app/middleware/logging.py 2>/dev/null \
		&& echo "✅ logging: OK" || echo "❌ logging: SYNTAX ERROR"
	@echo ""
	@echo "--- Disabled middleware in main.py ---"
	@grep -n "# .*Middleware\|# .*middleware\|# .*setup_unified" main.py || echo "✅ No disabled middleware found"

## T3: Find and remove .broken files
fix-broken-files:
	@echo "--- T3: Broken Files ---"
	@BROKEN=$$(find app -name "*.broken" 2>/dev/null); \
	if [ -z "$$BROKEN" ]; then \
		echo "✅ No .broken files found"; \
	else \
		echo "❌ Found broken files:"; \
		echo "$$BROKEN"; \
		echo ""; \
		read -p "Delete them? (y/n): " ans; \
		[ "$$ans" = "y" ] && rm -f $$BROKEN && echo "✅ Deleted" || echo "⊘ Skipped"; \
	fi

## T5: Check if pricing router can be re-enabled
fix-pricing-router:
	@echo "--- T5: Pricing Router ---"
	@python -m py_compile app/api/verification/pricing_endpoints.py 2>/dev/null \
		&& echo "✅ pricing_endpoints.py compiles OK — safe to uncomment in main.py" \
		|| echo "❌ pricing_endpoints.py has syntax errors — fix before uncommenting"
	@grep -n "pricing_router" main.py

## T7: List all temporarily disabled code
fix-commented-code:
	@echo "--- T7: Temporarily Disabled Code ---"
	@grep -rn "Temporarily disabled\|# TODO\|# FIXME\|# HACK" app/ main.py 2>/dev/null \
		| grep -v ".pyc" || echo "✅ None found"

## T8: Audit migration files for idempotency guards
fix-migrations:
	@echo "--- T8: Migration Idempotency Audit ---"
	@for f in alembic/versions/*.py; do \
		if grep -q "inspector\|column_exists\|table_exists\|IF NOT EXISTS" "$$f" 2>/dev/null; then \
			echo "✅ $$f"; \
		else \
			echo "⚠️  $$f — no idempotency guard detected"; \
		fi; \
	done

## T9: Validate required environment variables
fix-env:
	@echo "--- T9: Environment Variables ---"
	@python -c "\
import os; \
required = ['DATABASE_URL', 'SECRET_KEY', 'JWT_SECRET_KEY']; \
prod_extra = ['TEXTVERIFIED_API_KEY', 'PAYSTACK_SECRET_KEY', 'REDIS_URL']; \
env = os.getenv('ENVIRONMENT', 'development'); \
vars = required + (prod_extra if env == 'production' else []); \
missing = [v for v in vars if not os.getenv(v)]; \
[print(f'✅ {v}') for v in vars if os.getenv(v)]; \
[print(f'❌ MISSING: {v}') for v in missing]; \
exit(1 if missing else 0)\
"

# =============================================================
# TESTING
# =============================================================

## T4: Run integration tests with Docker test infrastructure
test-integration:
	@echo "--- T4: Integration Tests ---"
	docker-compose -f docker-compose.test.yml up -d
	@sleep 3
	TEST_DATABASE_URL=postgresql://test:test@localhost:5433/namaskah_test \
	TEST_REDIS_URL=redis://localhost:6380/0 \
	pytest tests/integration/ -v --tb=short -m "not requires_db or requires_db"
	docker-compose -f docker-compose.test.yml down

## T6: Generate HTML coverage report
test-coverage-report:
	pytest --cov=app --cov-report=html --cov-report=term-missing -q
	@echo ""
	@echo "📊 Report: htmlcov/index.html"
	@open htmlcov/index.html 2>/dev/null || xdg-open htmlcov/index.html 2>/dev/null || true

## T6: Fail CI if coverage below 50%
test-coverage-50:
	pytest --cov=app --cov-fail-under=50 --cov-report=term-missing -q

# =============================================================
# MONITORING
# =============================================================

## T10: Check local health endpoint
health-check:
	@curl -sf http://localhost:9527/health | python -m json.tool || echo "❌ App not running or health check failed"

## T10: Check external services health
health-external:
	@curl -sf http://localhost:9527/health/external | python -m json.tool || echo "❌ External health endpoint not available"

# =============================================================
# DEVELOPER EXPERIENCE
# =============================================================

## T11: Install pre-commit hooks
pre-commit-setup:
	pip install pre-commit
	python -c "\
import textwrap; \
open('.pre-commit-config.yaml','w').write(textwrap.dedent('''\
repos:\n\
  - repo: https://github.com/psf/black\n\
    rev: 24.1.1\n\
    hooks:\n\
      - id: black\n\
  - repo: https://github.com/pycqa/flake8\n\
    rev: 7.0.0\n\
    hooks:\n\
      - id: flake8\n\
        args: [--max-line-length=120]\n\
  - repo: https://github.com/pycqa/isort\n\
    rev: 5.13.2\n\
    hooks:\n\
      - id: isort\n\
  - repo: https://github.com/pre-commit/pre-commit-hooks\n\
    rev: v4.5.0\n\
    hooks:\n\
      - id: trailing-whitespace\n\
      - id: end-of-file-fixer\n\
      - id: check-yaml\n\
'''))"
	pre-commit install
	@echo "✅ Pre-commit hooks installed"