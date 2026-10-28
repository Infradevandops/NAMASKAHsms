.PHONY: ci fmt test push verify verify-local

ci: fmt test
	@echo "✅ All CI checks passed"

fmt:
	@black app/ --quiet
	@isort app/ --profile black --quiet
	@black --check app/ --quiet
	@isort --check-only app/ --profile black --quiet
	@flake8 app/ --count --select=E9,F63,F7,F82 --statistics
	@echo "✅ Formatting OK"

test:
	@pytest tests/unit/test_api_key_service.py \
	        tests/unit/test_analytics_service.py \
	        tests/unit/test_balance_service.py \
	        tests/unit/test_cache.py \
	        tests/unit/test_models.py \
	        tests/unit/test_utils.py \
	        tests/unit/test_carrier_lookup.py \
	        tests/unit/test_phone_validator.py \
	        tests/unit/test_stock_monitor.py \
	        --tb=short -q
	@echo "✅ Tests OK"

push: ci
	@git push origin main

# ---------------------------------------------------------------------------
# Post-deploy smoke checks — runs against production
# Usage: make verify
# ---------------------------------------------------------------------------
PROD=https://vrenum.app

verify:
	@echo "🔍 Running production smoke checks against $(PROD)..."
	@echo ""

	@echo "[1/7] Health endpoint"
	@STATUS=$$(curl -s -o /dev/null -w "%{http_code}" $(PROD)/health); \
	 if [ "$$STATUS" = "200" ]; then echo "  ✅ /health → $$STATUS"; \
	 else echo "  ❌ /health → $$STATUS"; exit 1; fi

	@echo "[2/7] Detailed health (DB + Redis + TextVerified)"
	@BODY=$$(curl -s $(PROD)/api/monitoring/health/detailed); \
	 STATUS=$$(echo $$BODY | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','unknown'))" 2>/dev/null); \
	 BACKEND=$$(echo $$BODY | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('checks',{}).get('cache',{}).get('backend','unknown'))" 2>/dev/null); \
	 if [ "$$STATUS" = "healthy" ]; then echo "  ✅ status=$$STATUS cache=$$BACKEND"; \
	 else echo "  ⚠️  status=$$STATUS cache=$$BACKEND (check Sentry)"; fi

	@echo "[3/7] Stock availability endpoint"
	@BODY=$$(curl -s $(PROD)/api/services/stock); \
	 TOTAL=$$(echo $$BODY | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('total',0))" 2>/dev/null); \
	 AVAIL=$$(echo $$BODY | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('available',0))" 2>/dev/null); \
	 if [ "$$TOTAL" -gt "0" ] 2>/dev/null; then echo "  ✅ total=$$TOTAL available=$$AVAIL"; \
	 else echo "  ❌ /api/services/stock returned total=$$TOTAL (stock monitor may not have run yet)"; exit 1; fi

	@echo "[4/7] Auth endpoint reachable"
	@STATUS=$$(curl -s -o /dev/null -w "%{http_code}" -X POST $(PROD)/api/auth/login \
	  -H "Content-Type: application/json" \
	  -d '{"email":"smoke@test.invalid","password":"x"}'); \
	 if [ "$$STATUS" = "401" ] || [ "$$STATUS" = "422" ]; then echo "  ✅ /api/auth/login → $$STATUS (reachable)"; \
	 else echo "  ❌ /api/auth/login → $$STATUS (unexpected)"; exit 1; fi

	@echo "[5/7] Wallet endpoint requires auth"
	@STATUS=$$(curl -s -o /dev/null -w "%{http_code}" $(PROD)/api/wallet/balance); \
	 if [ "$$STATUS" = "401" ] || [ "$$STATUS" = "403" ]; then echo "  ✅ /api/wallet/balance → $$STATUS (auth gated)"; \
	 else echo "  ❌ /api/wallet/balance → $$STATUS (should be 401/403)"; exit 1; fi

	@echo "[6/7] Verify endpoint requires auth"
	@STATUS=$$(curl -s -o /dev/null -w "%{http_code}" -X POST $(PROD)/api/verification/request \
	  -H "Content-Type: application/json" -d '{}'); \
	 if [ "$$STATUS" = "401" ] || [ "$$STATUS" = "403" ] || [ "$$STATUS" = "422" ]; then echo "  ✅ /api/verification/request → $$STATUS (auth gated)"; \
	 else echo "  ❌ /api/verification/request → $$STATUS (unexpected)"; exit 1; fi

	@echo "[7/7] Static assets reachable"
	@STATUS=$$(curl -s -o /dev/null -w "%{http_code}" $(PROD)/static/js/verification-flow.js); \
	 if [ "$$STATUS" = "200" ]; then echo "  ✅ /static/js/verification-flow.js → $$STATUS"; \
	 else echo "  ❌ /static/js/verification-flow.js → $$STATUS"; exit 1; fi

	@echo "[8/9] User profile endpoint requires auth"
	@STATUS=$$(curl -s -o /dev/null -w "%{http_code}" $(PROD)/api/user/me); \
	 if [ "$$STATUS" = "401" ]; then echo "  ✅ /api/user/me → $$STATUS (auth gated)"; \
	 else echo "  ❌ /api/user/me → $$STATUS (expected 401)"; exit 1; fi

	@echo "[9/9] Rentals endpoint requires auth"
	@STATUS=$$(curl -s -o /dev/null -w "%{http_code}" $(PROD)/api/rentals/active); \
	 if [ "$$STATUS" = "401" ]; then echo "  ✅ /api/rentals/active → $$STATUS (auth gated)"; \
	 else echo "  ❌ /api/rentals/active → $$STATUS (expected 401)"; exit 1; fi

	@echo ""
	@echo "✅ All smoke checks passed — $(PROD) is healthy"

# ---------------------------------------------------------------------------
# Local smoke checks — runs against localhost:8000
# Usage: make verify-local
# ---------------------------------------------------------------------------
verify-local:
	@$(MAKE) verify PROD=http://localhost:8000
