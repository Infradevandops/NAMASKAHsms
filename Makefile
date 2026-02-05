# Namaskah SMS Analytics - Development Makefile

.PHONY: install lint format test security-check build clean help

# Default target
help:
	@echo "Available commands:"
	@echo "  install        - Install dependencies"
	@echo "  lint          - Run ESLint"
	@echo "  lint-fix      - Run ESLint with auto-fix"
	@echo "  format        - Format code with Prettier"
	@echo "  test          - Run tests"
	@echo "  test-watch    - Run tests in watch mode"
	@echo "  test-coverage - Run tests with coverage"
	@echo "  security-check - Run security checks"
	@echo "  build         - Build and validate everything"
	@echo "  clean         - Clean build artifacts"

# Install dependencies
install:
	npm install
	pip install -r requirements.txt
	pip install -r requirements-test.txt

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
	npm run test
	pytest app/tests/ -v --cov=app --cov-report=html

test-watch:
	npm run test:watch

test-coverage:
	npm run test:coverage
	pytest app/tests/ -v --cov=app --cov-report=html --cov-report=term

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
	npm run lint
	pytest app/tests/ -v
	bandit -r app/ -ll
	@echo "✅ Production checks passed"