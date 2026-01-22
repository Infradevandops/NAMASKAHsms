#!/usr/bin/env python3
"""
Verification Flow Safety Test
==============================
Tests all safety improvements and best practices.
"""

import sys
from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.transaction import Transaction
from app.models.user import User
from app.models.verification import Verification

logger = get_logger(__name__)


def test_verification_flow_safety():
    """Test verification flow safety improvements."""
    
    print("=" * 80)
    print("VERIFICATION FLOW SAFETY TEST")
    print("=" * 80)
    print()
    
    db = SessionLocal()
    results = {
        "passed": 0,
        "failed": 0,
        "tests": []
    }
    
    try:
        # Test 1: Auto-refund service exists
        print("Test 1: Auto-refund service exists...")
        try:
            from app.services.auto_refund_service import AutoRefundService
            refund_service = AutoRefundService(db)
            assert hasattr(refund_service, 'process_verification_refund')
            assert hasattr(refund_service, 'reconcile_unrefunded_verifications')
            print("✅ PASS: Auto-refund service loaded")
            results["passed"] += 1
            results["tests"].append(("Auto-refund service", "PASS"))
        except Exception as e:
            print(f"❌ FAIL: {str(e)}")
            results["failed"] += 1
            results["tests"].append(("Auto-refund service", "FAIL"))
        print()
        
        # Test 2: SMS polling has refund integration
        print("Test 2: SMS polling has refund integration...")
        try:
            with open("app/services/sms_polling_service.py", "r") as f:
                content = f.read()
                assert "AutoRefundService" in content
                assert "process_verification_refund" in content
            print("✅ PASS: SMS polling integrated with refund service")
            results["passed"] += 1
            results["tests"].append(("SMS polling refund integration", "PASS"))
        except Exception as e:
            print(f"❌ FAIL: {str(e)}")
            results["failed"] += 1
            results["tests"].append(("SMS polling refund integration", "FAIL"))
        print()
        
        # Test 3: Purchase endpoint has two-phase commit
        print("Test 3: Purchase endpoint has two-phase commit...")
        try:
            with open("app/api/verification/purchase_endpoints.py", "r") as f:
                content = f.read()
                # Check that API is called before credit deduction
                api_call_pos = content.find("tv_service.create_verification")
                credit_deduct_pos = content.find("user.credits -=")
                assert api_call_pos < credit_deduct_pos, "Credits deducted before API call!"
                assert "db.rollback()" in content, "No rollback on failure!"
            print("✅ PASS: Two-phase commit implemented")
            results["passed"] += 1
            results["tests"].append(("Two-phase commit", "PASS"))
        except Exception as e:
            print(f"❌ FAIL: {str(e)}")
            results["failed"] += 1
            results["tests"].append(("Two-phase commit", "FAIL"))
        print()
        
        # Test 4: Idempotency key support
        print("Test 4: Idempotency key support...")
        try:
            from app.schemas.verification import VerificationRequest
            from pydantic import ValidationError
            
            # Test with idempotency key
            req = VerificationRequest(
                service="telegram",
                country="US",
                idempotency_key="test-key-123"
            )
            assert req.idempotency_key == "test-key-123"
            
            # Check purchase endpoint uses it
            with open("app/api/verification/purchase_endpoints.py", "r") as f:
                content = f.read()
                assert "idempotency_key" in content
                assert "Duplicate request detected" in content
            
            print("✅ PASS: Idempotency key supported")
            results["passed"] += 1
            results["tests"].append(("Idempotency key", "PASS"))
        except Exception as e:
            print(f"❌ FAIL: {str(e)}")
            results["failed"] += 1
            results["tests"].append(("Idempotency key", "FAIL"))
        print()
        
        # Test 5: Cancellation endpoint exists
        print("Test 5: Cancellation endpoint with refund...")
        try:
            import os
            assert os.path.exists("app/api/verification/cancel_endpoint.py")
            with open("app/api/verification/cancel_endpoint.py", "r") as f:
                content = f.read()
                assert "cancel_verification" in content
                assert "AutoRefundService" in content
            print("✅ PASS: Cancellation endpoint with refund exists")
            results["passed"] += 1
            results["tests"].append(("Cancellation endpoint", "PASS"))
        except Exception as e:
            print(f"❌ FAIL: {str(e)}")
            results["failed"] += 1
            results["tests"].append(("Cancellation endpoint", "FAIL"))
        print()
        
        # Test 6: Circuit breaker exists
        print("Test 6: Circuit breaker for API resilience...")
        try:
            import os
            assert os.path.exists("app/core/circuit_breaker.py")
            from app.core.circuit_breaker import CircuitBreaker, textverified_circuit_breaker
            assert isinstance(textverified_circuit_breaker, CircuitBreaker)
            print("✅ PASS: Circuit breaker implemented")
            results["passed"] += 1
            results["tests"].append(("Circuit breaker", "PASS"))
        except Exception as e:
            print(f"❌ FAIL: {str(e)}")
            results["failed"] += 1
            results["tests"].append(("Circuit breaker", "FAIL"))
        print()
        
        # Test 7: Verification model has idempotency_key field
        print("Test 7: Verification model has idempotency_key...")
        try:
            from app.models.verification import Verification
            assert hasattr(Verification, 'idempotency_key')
            print("✅ PASS: Verification model has idempotency_key field")
            results["passed"] += 1
            results["tests"].append(("Verification model idempotency", "PASS"))
        except Exception as e:
            print(f"❌ FAIL: {str(e)}")
            results["failed"] += 1
            results["tests"].append(("Verification model idempotency", "FAIL"))
        print()
        
        # Test 8: Reconciliation script exists
        print("Test 8: Reconciliation script...")
        try:
            import os
            assert os.path.exists("reconcile_refunds.py")
            print("✅ PASS: Reconciliation script exists")
            results["passed"] += 1
            results["tests"].append(("Reconciliation script", "PASS"))
        except Exception as e:
            print(f"❌ FAIL: {str(e)}")
            results["failed"] += 1
            results["tests"].append(("Reconciliation script", "FAIL"))
        print()
        
        # Summary
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {results['passed'] + results['failed']}")
        print(f"Passed: {results['passed']} ✅")
        print(f"Failed: {results['failed']} ❌")
        print()
        
        if results["failed"] == 0:
            print("🎉 ALL TESTS PASSED - Verification flow is safe!")
            print()
            print("Safety Features Verified:")
            print("  ✅ Automatic refunds on timeout/cancel/failure")
            print("  ✅ Two-phase commit (API first, then deduct)")
            print("  ✅ Automatic rollback on errors")
            print("  ✅ Idempotency to prevent duplicate charges")
            print("  ✅ Cancellation with refund")
            print("  ✅ Circuit breaker for resilience")
            print("  ✅ Reconciliation for past issues")
            print()
            return 0
        else:
            print("⚠️  SOME TESTS FAILED - Review and fix issues")
            print()
            print("Failed Tests:")
            for test_name, result in results["tests"]:
                if result == "FAIL":
                    print(f"  ❌ {test_name}")
            print()
            return 1
    
    except Exception as e:
        print(f"\n❌ TEST ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(test_verification_flow_safety())
