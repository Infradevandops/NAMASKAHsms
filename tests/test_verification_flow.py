"""Comprehensive verification flow test."""

import asyncio
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect, text

from app.core.database import SessionLocal
from app.models.user import User
from app.models.verification import Verification

print("=" * 60)
print("VERIFICATION FLOW DEEP ASSESSMENT")
print("=" * 60)

issues = []

# Test 1: Database Schema
print("\n1️⃣  Testing Database Schema...")
try:
    db = SessionLocal()
    engine = db.get_bind()
    inspector = inspect(engine)

    # Check verifications table
    columns = [col["name"] for col in inspector.get_columns("verifications")]

    required_columns = [
        "id",
        "user_id",
        "service_name",
        "phone_number",
        "country",
        "capability",
        "status",
        "cost",
        "activation_id",
        "provider",
        "idempotency_key",
        "sms_code",
        "sms_text",
        "created_at",
    ]

    missing = [col for col in required_columns if col not in columns]
    if missing:
        issues.append(f"❌ Missing columns in verifications table: {missing}")
        print(f"   ❌ Missing columns: {missing}")
    else:
        print("   ✅ All required columns present")

    # Check indexes
    indexes = inspector.get_indexes("verifications")
    index_names = [idx["name"] for idx in indexes]

    if "ix_verifications_idempotency_key" not in index_names:
        issues.append("⚠️  Missing index on idempotency_key")
        print("   ⚠️  Missing index on idempotency_key")
    else:
        print("   ✅ Idempotency index exists")

except Exception as e:
    issues.append(f"❌ Database schema check failed: {e}")
    print(f"   ❌ Error: {e}")

# Test 2: API Endpoint Availability
print("\n2️⃣  Testing API Endpoints...")
try:
    from app.api.verification.consolidated_verification import router

    routes = [route.path for route in router.routes]
    required_routes = [
        "/verify/services",
        "/verify/create",
        "/verify/{verification_id}",
        "/verify/{verification_id}/status",
        "/verify/history",
    ]

    for route in required_routes:
        if any(r.startswith(route.replace("{", "").replace("}", "")) for r in routes):
            print(f"   ✅ {route}")
        else:
            issues.append(f"❌ Missing route: {route}")
            print(f"   ❌ {route}")

except Exception as e:
    issues.append(f"❌ API endpoint check failed: {e}")
    print(f"   ❌ Error: {e}")

# Test 3: Frontend JavaScript
print("\n3️⃣  Testing Frontend JavaScript...")
try:
    with open("static/js/verification.js", "r") as f:
        js_content = f.read()

    # Check for critical functions
    critical_functions = [
        "purchaseVerification",
        "startPolling",
        "loadServices",
        "selectService",
        "cancelVerification",
        "checkTierAccess",
    ]

    for func in critical_functions:
        if f"function {func}" in js_content or f"async function {func}" in js_content:
            print(f"   ✅ {func}()")
        else:
            issues.append(f"❌ Missing function: {func}()")
            print(f"   ❌ {func}()")

    # Check for idempotency_key in request
    if "idempotency_key" in js_content:
        print("   ✅ Idempotency key generation present")
    else:
        issues.append("⚠️  Idempotency key not generated in frontend")
        print("   ⚠️  Idempotency key not generated")

except Exception as e:
    issues.append(f"❌ Frontend check failed: {e}")
    print(f"   ❌ Error: {e}")

# Test 4: Model Validation
print("\n4️⃣  Testing Model Validation...")
try:
    # Check if Verification model has all required fields
    from app.models.verification import Verification

    model_columns = [col.name for col in Verification.__table__.columns]

    if "idempotency_key" in model_columns:
        print("   ✅ Verification model has idempotency_key")
    else:
        issues.append("❌ Verification model missing idempotency_key")
        print("   ❌ Model missing idempotency_key")

except Exception as e:
    issues.append(f"❌ Model validation failed: {e}")
    print(f"   ❌ Error: {e}")

# Test 5: Service Integration
print("\n5️⃣  Testing Service Integration...")
try:
    from app.services.textverified_service import TextVerifiedService

    tv = TextVerifiedService()

    if tv.enabled:
        print("   ✅ TextVerified service enabled")
    else:
        issues.append("⚠️  TextVerified service disabled")
        print("   ⚠️  TextVerified service disabled")

    # Check if API key is set
    if tv.api_key:
        print("   ✅ API key configured")
    else:
        issues.append("❌ TextVerified API key not configured")
        print("   ❌ API key not configured")

except Exception as e:
    issues.append(f"❌ Service integration check failed: {e}")
    print(f"   ❌ Error: {e}")

# Test 6: Polling Service
print("\n6️⃣  Testing Polling Service...")
try:
    from app.services.sms_polling_service import SMSPollingService

    print("   ✅ SMS polling service importable")

    # Check if polling queries will work
    try:
        db = SessionLocal()
        test_query = (
            db.query(Verification)
            .filter(
                Verification.status == "pending",
                Verification.provider == "textverified",
            )
            .limit(1)
            .all()
        )
        print("   ✅ Polling queries work")
    except Exception as e:
        issues.append(f"❌ Polling query failed: {e}")
        print(f"   ❌ Polling query failed: {e}")

except Exception as e:
    issues.append(f"❌ Polling service check failed: {e}")
    print(f"   ❌ Error: {e}")

# Test 7: Error Handling
print("\n7️⃣  Testing Error Handling...")
try:
    from app.api.verification.consolidated_verification import create_safe_error_detail

    test_error = Exception("Test error with sensitive data: password=secret123")
    safe_detail = create_safe_error_detail(test_error)

    if len(safe_detail) <= 100:
        print("   ✅ Error sanitization works")
    else:
        issues.append("⚠️  Error messages not properly truncated")
        print("   ⚠️  Error messages not properly truncated")

except Exception as e:
    issues.append(f"❌ Error handling check failed: {e}")
    print(f"   ❌ Error: {e}")

# Test 8: Frontend-Backend Integration
print("\n8️⃣  Testing Frontend-Backend Integration...")
try:
    # Check if API endpoint matches frontend call
    with open("static/js/verification.js", "r") as f:
        js_content = f.read()

    if "'/api/v1/verify/create'" in js_content:
        print("   ✅ Frontend calls correct endpoint")
    else:
        issues.append("❌ Frontend endpoint mismatch")
        print("   ❌ Frontend endpoint mismatch")

    # Check if response fields match
    if "phone_number" in js_content and "fallback_applied" in js_content:
        print("   ✅ Response fields handled")
    else:
        issues.append("⚠️  Some response fields may not be handled")
        print("   ⚠️  Some response fields may not be handled")

except Exception as e:
    issues.append(f"❌ Integration check failed: {e}")
    print(f"   ❌ Error: {e}")

# Summary
print("\n" + "=" * 60)
print("ASSESSMENT SUMMARY")
print("=" * 60)

if not issues:
    print("✅ All checks passed!")
else:
    print(f"⚠️  Found {len(issues)} issue(s):\n")
    for i, issue in enumerate(issues, 1):
        print(f"{i}. {issue}")

print("\n" + "=" * 60)
print("RECOMMENDATIONS")
print("=" * 60)

recommendations = []

if any("idempotency_key" in issue for issue in issues):
    recommendations.append("1. Run: python scripts/fix_production_idempotency.py")

if any("TextVerified" in issue for issue in issues):
    recommendations.append("2. Set TEXTVERIFIED_API_KEY in environment")

if any("endpoint" in issue.lower() for issue in issues):
    recommendations.append("3. Check API route registration in main.py")

if any("polling" in issue.lower() for issue in issues):
    recommendations.append("4. Restart polling services")

if recommendations:
    for rec in recommendations:
        print(f"   {rec}")
else:
    print("   No immediate actions required")

print("\n" + "=" * 60)
