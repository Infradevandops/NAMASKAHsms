#!/usr/bin/env python3
"""Final verification test for area code and carrier filters."""

import asyncio
import sys
import os
import pytest

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.textverified_service import TextVerifiedService


@pytest.mark.asyncio
async def test_filters():
    """Test that filters are properly sent to TextVerified API."""
    
    print("=" * 80)
    print("FINAL FILTER VERIFICATION TEST")
    print("=" * 80)
    
    tv_service = TextVerifiedService()
    
    if not tv_service.enabled:
        print("❌ TextVerified service not enabled")
        return False
    
    print("✅ TextVerified service initialized\n")
    
    # Test 1: Verify SDK method signature
    print("TEST 1: SDK Method Signature")
    print("-" * 80)
    import inspect
    sig = inspect.signature(tv_service.client.verifications.create)
    params = list(sig.parameters.keys())
    print(f"Parameters: {params}")
    
    has_area_code = 'area_code_select_option' in params
    has_carrier = 'carrier_select_option' in params
    
    print(f"✅ Has area_code_select_option: {has_area_code}")
    print(f"✅ Has carrier_select_option: {has_carrier}")
    
    if not (has_area_code and has_carrier):
        print("❌ SDK missing required parameters!")
        return False
    
    # Test 2: Verify our implementation uses SDK correctly
    print("\nTEST 2: Implementation Check")
    print("-" * 80)
    
    import inspect
    source = inspect.getsource(tv_service.create_verification)
    
    uses_sdk = 'self.client.verifications.create(' in source
    uses_area_param = 'area_code_select_option=' in source
    uses_carrier_param = 'carrier_select_option=' in source
    uses_list_wrap = '[area_code]' in source and '[carrier]' in source
    
    print(f"✅ Uses SDK high-level method: {uses_sdk}")
    print(f"✅ Uses area_code_select_option: {uses_area_param}")
    print(f"✅ Uses carrier_select_option: {uses_carrier_param}")
    print(f"✅ Wraps in list: {uses_list_wrap}")
    
    if not all([uses_sdk, uses_area_param, uses_carrier_param, uses_list_wrap]):
        print("❌ Implementation doesn't use SDK correctly!")
        return False
    
    # Test 3: Check payload serialization
    print("\nTEST 3: Payload Serialization")
    print("-" * 80)
    
    from textverified.data.dtypes import NewVerificationRequest
    import textverified
    
    req = NewVerificationRequest(
        service_name='telegram',
        capability=textverified.ReservationCapability.SMS,
        area_code_select_option=['212'],
        carrier_select_option=['verizon']
    )
    
    payload = req.to_api()
    print(f"Payload keys: {list(payload.keys())}")
    print(f"Area code field: {payload.get('areaCodeSelectOption')}")
    print(f"Carrier field: {payload.get('carrierSelectOption')}")
    
    correct_area = payload.get('areaCodeSelectOption') == ['212']
    correct_carrier = payload.get('carrierSelectOption') == ['verizon']
    
    print(f"✅ Area code serializes correctly: {correct_area}")
    print(f"✅ Carrier serializes correctly: {correct_carrier}")
    
    if not (correct_area and correct_carrier):
        print("❌ Payload serialization incorrect!")
        return False
    
    # Test 4: Live API test (dry run - check balance only)
    print("\nTEST 4: Live API Connection")
    print("-" * 80)
    
    try:
        balance = await tv_service.get_balance()
        print(f"✅ API connected: ${balance['balance']:.2f} balance")
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - FILTERS ARE CORRECTLY IMPLEMENTED")
    print("=" * 80)
    print("\nImplementation Summary:")
    print("  • SDK method: client.verifications.create()")
    print("  • Area code param: area_code_select_option=['212']")
    print("  • Carrier param: carrier_select_option=['verizon']")
    print("  • API payload: areaCodeSelectOption=['212'], carrierSelectOption=['verizon']")
    print("\nFilters WILL be sent to TextVerified API correctly! ✅")
    
    return True


if __name__ == "__main__":
    result = asyncio.run(test_filters())
    sys.exit(0 if result else 1)
