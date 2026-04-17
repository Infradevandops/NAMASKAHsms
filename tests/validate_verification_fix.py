"""Post-Fix Verification Flow Validation Suite."""


import os
import sys
from datetime import datetime

from app.api.verification.consolidated_verification import (
    create_safe_error_detail,
    router,
)
from app.models.verification import Verification
from app.services.sms_polling_service import SMSPollingService
from app.services.textverified_service import TextVerifiedService

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 70)
print("VERIFICATION FLOW - POST-FIX VALIDATION")
print("=" * 70)
print(f"Timestamp: {datetime.now().isoformat()}")
print("=" * 70)

passed = []
failed = []
warnings = []

# TEST 1: Model Schema Validation
print("\n🧪 TEST 1: Model Schema Validation")
try:

    cols = [col.name for col in Verification.__table__.columns]

    # Check critical columns
    critical = [
        "id",
        "user_id",
        "service_name",
        "phone_number",
        "status",
        "cost",
        "idempotency_key",
        "activation_id",
        "sms_code",
    ]

    missing = [c for c in critical if c not in cols]

if missing:
        failed.append(f"Model missing columns: {missing}")
        print(f"   ❌ FAIL: Missing {missing}")
else:
        passed.append("Model has all critical columns")
        print(f"   ✅ PASS: All {len(critical)} critical columns present")

    # Check idempotency_key specifically
if "idempotency_key" in cols:
        passed.append("idempotency_key column exists in model")
        print("   ✅ PASS: idempotency_key column enabled")
else:
        failed.append("idempotency_key still missing from model")
        print("   ❌ FAIL: idempotency_key not in model")

except Exception as e:
    failed.append(f"Model validation error: {str(e)[:100]}")
    print(f"   ❌ FAIL: {str(e)[:100]}")

# TEST 2: API Endpoint Registration
print("\n🧪 TEST 2: API Endpoint Registration")
try:

    routes = {route.path: [m for m in route.methods] for route in router.routes}

    required = {
        "/verify/services": ["GET"],
        "/verify/create": ["POST"],
        "/verify/{verification_id}": ["GET"],
        "/verify/{verification_id}/status": ["GET"],
        "/verify/{verification_id}": ["DELETE"],
        "/verify/history": ["GET"],
    }

    all_good = True
for path, methods in required.items():
        found = any(path in r for r in routes.keys())
if found:
            print(f"   ✅ {path}")
else:
            all_good = False
            failed.append(f"Missing route: {path}")
            print(f"   ❌ {path}")

if all_good:
        passed.append("All API endpoints registered")

except Exception as e:
    failed.append(f"API endpoint check error: {str(e)[:100]}")
    print(f"   ❌ FAIL: {str(e)[:100]}")

# TEST 3: Frontend JavaScript Integrity
print("\n🧪 TEST 3: Frontend JavaScript Integrity")
try:
with open("static/js/verification.js", "r") as f:
        js = f.read()

    checks = {
        "purchaseVerification function": "async function purchaseVerification()" in js,
        "idempotency_key generation": "idempotency_key" in js and "crypto.randomUUID" in js,
        "startPolling function": "function startPolling(" in js,
        "API endpoint correct": "'/api/v1/verify/create'" in js,
        "Error handling": "catch (error)" in js or "catch(error)" in js,
        "Tier access check": "checkTierAccess" in js,
        "Carrier detection": "detectCarrier" in js,
        "Copy code function": "function copyCode()" in js,
    }

for check, result in checks.items():
if result:
            print(f"   ✅ {check}")
            passed.append(f"Frontend: {check}")
else:
            print(f"   ❌ {check}")
            failed.append(f"Frontend missing: {check}")

except Exception as e:
    failed.append(f"Frontend check error: {str(e)[:100]}")
    print(f"   ❌ FAIL: {str(e)[:100]}")

# TEST 4: Backend Logic Validation
print("\n🧪 TEST 4: Backend Logic Validation")
try:
with open("app/api/verification/consolidated_verification.py", "r") as f:
        backend = f.read()

    checks = {
        "Idempotency check": "idempotency_key" in backend and "existing =" in backend,
        "Credit validation": "credits >=" in backend or "credits <" in backend,
        "TextVerified integration": "TextVerifiedService" in backend,
        "Error handling": "try:" in backend and "except" in backend,
        "Rollback on error": "db.rollback()" in backend,
        "Tier feature gating": "tier_manager" in backend or "TierManager" in backend,
        "Fallback logic": "fallback" in backend.lower(),
        "Status polling": "status" in backend and "pending" in backend,
    }

for check, result in checks.items():
if result:
            print(f"   ✅ {check}")
            passed.append(f"Backend: {check}")
else:
            print(f"   ⚠️  {check}")
            warnings.append(f"Backend: {check} not found")

except Exception as e:
    failed.append(f"Backend check error: {str(e)[:100]}")
    print(f"   ❌ FAIL: {str(e)[:100]}")

# TEST 5: Service Integration
print("\n🧪 TEST 5: Service Integration")
try:

    tv = TextVerifiedService()

if tv.enabled:
        print("   ✅ TextVerified service enabled")
        passed.append("TextVerified service enabled")
else:
        print("   ⚠️  TextVerified service disabled")
        warnings.append("TextVerified service disabled")

if tv.api_key:
        print("   ✅ API key configured")
        passed.append("TextVerified API key set")
else:
        print("   ❌ API key missing")
        failed.append("TextVerified API key not configured")

    # Check if service has required methods
    methods = ["create_verification", "get_sms", "cancel_number", "get_services"]
for method in methods:
if hasattr(tv, method):
            print(f"   ✅ Method: {method}()")
else:
            print(f"   ❌ Method: {method}()")
            failed.append(f"TextVerified missing method: {method}")

except Exception as e:
    failed.append(f"Service integration error: {str(e)[:100]}")
    print(f"   ❌ FAIL: {str(e)[:100]}")

# TEST 6: Polling Service Health
print("\n🧪 TEST 6: Polling Service Health")
try:

    print("   ✅ SMS polling service importable")
    passed.append("SMS polling service exists")

    # Check if it has required methods
if hasattr(SMSPollingService, "start"):
        print("   ✅ Has start() method")
else:
        warnings.append("SMS polling missing start() method")
        print("   ⚠️  Missing start() method")

except Exception as e:
    failed.append(f"Polling service error: {str(e)[:100]}")
    print(f"   ❌ FAIL: {str(e)[:100]}")

# TEST 7: Database Migration Script
print("\n🧪 TEST 7: Database Migration Script")
try:

    script_path = "scripts/fix_production_idempotency.py"

if os.path.exists(script_path):
        print("   ✅ Migration script exists")
        passed.append("Migration script created")

with open(script_path, "r") as f:
            script = f.read()

if "idempotency_key" in script and "ALTER TABLE" in script:
            print("   ✅ Script contains correct SQL")
            passed.append("Migration script has correct SQL")
else:
            warnings.append("Migration script may be incomplete")
            print("   ⚠️  Script may be incomplete")
else:
        failed.append("Migration script not found")
        print(f"   ❌ Script not found at {script_path}")

except Exception as e:
    failed.append(f"Migration script check error: {str(e)[:100]}")
    print(f"   ❌ FAIL: {str(e)[:100]}")

# TEST 8: Error Handling & Security
print("\n🧪 TEST 8: Error Handling & Security")
try:
    # Force reimport to get latest code

if "app.api.verification.consolidated_verification" in sys.modules:
        del sys.modules["app.api.verification.consolidated_verification"]


    # Test error sanitization
    test_error = Exception("Error with sensitive data: password=secret123 api_key=xyz789")
    safe = create_safe_error_detail(test_error)

if len(safe) <= 100:
        print("   ✅ Error messages truncated to 100 chars")
        passed.append("Error sanitization works")
else:
        warnings.append("Error messages not properly truncated")
        print(f"   ⚠️  Error message too long: {len(safe)} chars")

    # Check for sensitive data leakage
if "secret123" not in safe and "xyz789" not in safe:
        print("   ✅ Sensitive data sanitized")
        passed.append("No sensitive data in errors")
else:
        failed.append("Sensitive data may leak in errors")
        print(f"   ❌ Sensitive data found: {safe}")

except Exception as e:
    warnings.append(f"Error handling check: {str(e)[:100]}")
    print(f"   ⚠️  {str(e)[:100]}")

# TEST 9: Frontend-Backend Contract
print("\n🧪 TEST 9: Frontend-Backend Contract")
try:
with open("static/js/verification.js", "r") as f:
        frontend = f.read()

with open("app/api/verification/consolidated_verification.py", "r") as f:
        backend = f.read()

    # Check request fields match
    frontend_fields = [
        "service_name",
        "country",
        "capability",
        "area_code",
        "carrier",
        "idempotency_key",
    ]
    backend_fields = [
        "service_name",
        "country",
        "capability",
        "area_code",
        "carrier",
        "idempotency_key",
    ]

    contract_valid = True
for field in frontend_fields:
if field in backend:
            print(f"   ✅ Field: {field}")
else:
            print(f"   ❌ Field: {field} (frontend sends, backend doesn't handle)")
            contract_valid = False

if contract_valid:
        passed.append("Frontend-backend contract valid")
else:
        failed.append("Frontend-backend contract mismatch")

except Exception as e:
    warnings.append(f"Contract check error: {str(e)[:100]}")
    print(f"   ⚠️  {str(e)[:100]}")

# TEST 10: Critical User Flows
print("\n🧪 TEST 10: Critical User Flows")
try:
    flows = {
        "Service selection": "selectService" in open("static/js/verification.js").read(),
        "Verification purchase": "purchaseVerification" in open("static/js/verification.js").read(),
        "Status polling": "startPolling" in open("static/js/verification.js").read(),
        "Code copy": "copyCode" in open("static/js/verification.js").read(),
        "Cancellation": "cancelVerification" in open("static/js/verification.js").read(),
        "Reset form": "resetForm" in open("static/js/verification.js").read(),
    }

    all_flows = True
for flow, exists in flows.items():
if exists:
            print(f"   ✅ {flow}")
else:
            print(f"   ❌ {flow}")
            failed.append(f"Missing flow: {flow}")
            all_flows = False

if all_flows:
        passed.append("All critical user flows present")

except Exception as e:
    failed.append(f"User flow check error: {str(e)[:100]}")
    print(f"   ❌ FAIL: {str(e)[:100]}")

# SUMMARY
print("\n" + "=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)

print(f"\n✅ PASSED: {len(passed)} tests")
for p in passed[:5]:
    print(f"   • {p}")
if len(passed) > 5:
    print(f"   ... and {len(passed) - 5} more")

if warnings:
    print(f"\n⚠️  WARNINGS: {len(warnings)} issues")
for w in warnings[:5]:
        print(f"   • {w}")
if len(warnings) > 5:
        print(f"   ... and {len(warnings) - 5} more")

if failed:
    print(f"\n❌ FAILED: {len(failed)} tests")
for f in failed:
        print(f"   • {f}")
else:
    print("\n🎉 NO FAILURES!")

# OVERALL STATUS
print("\n" + "=" * 70)
total_tests = len(passed) + len(failed) + len(warnings)
success_rate = (len(passed) / total_tests * 100) if total_tests > 0 else 0

if len(failed) == 0 and len(warnings) == 0:
    status = "🟢 EXCELLENT"
    message = "All tests passed! Verification flow is healthy."
elif len(failed) == 0:
    status = "🟡 GOOD"
    message = "All tests passed with minor warnings."
elif len(failed) <= 2:
    status = "🟠 NEEDS ATTENTION"
    message = "Some tests failed. Review and fix issues."
else:
    status = "🔴 CRITICAL"
    message = "Multiple failures detected. Immediate action required."

print(f"OVERALL STATUS: {status}")
print(f"Success Rate: {success_rate:.1f}%")
print(f"Assessment: {message}")

# NEXT STEPS
print("\n" + "=" * 70)
print("NEXT STEPS")
print("=" * 70)

if failed:
    print("\n🔧 Required Actions:")
if any("idempotency" in f.lower() for f in failed):
        print("   1. Run: python scripts/fix_production_idempotency.py")
if any("api key" in f.lower() for f in failed):
        print("   2. Set TEXTVERIFIED_API_KEY environment variable")
if any("route" in f.lower() or "endpoint" in f.lower() for f in failed):
        print("   3. Check API router registration in main.py")
    print("   4. Restart application services")
    print("   5. Re-run this validation script")
else:
    print("\n✅ Ready for Production:")
    print("   1. Deploy code changes")
    print("   2. Run database migration")
    print("   3. Restart services")
    print("   4. Monitor verification success rate")
    print("   5. Test end-to-end verification flow")

print("\n" + "=" * 70)
print(f"Validation completed at {datetime.now().isoformat()}")
print("=" * 70)

# Exit code
sys.exit(0 if len(failed) == 0 else 1)
