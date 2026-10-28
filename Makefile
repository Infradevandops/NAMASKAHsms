.PHONY: ci fmt test push

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
	        --tb=short -q
	@echo "✅ Tests OK"

push: ci
	@git push origin main
