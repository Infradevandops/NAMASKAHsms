#!/usr/bin/env python3
"""
Test script to verify TextVerified API support for area codes.

Tests:
1. Voice verification with area code
2. Voice verification without area code
3. Rentals with area code (if supported)
4. Compare SMS vs Voice behavior

Usage:
    python3 scripts/test_textverified_area_codes.py
"""

import asyncio
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.logging import get_logger
from app.services.textverified_service import TextVerifiedService

logger = get_logger(__name__)


async def test_sms_with_area_code():
    """Test SMS verification with area code (baseline - known to work)"""
    print("\n" + "=" * 80)
    print("TEST 1: SMS Verification with Area Code (Baseline)")
    print("=" * 80)

    service = TextVerifiedService()

    if not service.enabled:
        print("❌ TextVerified service not enabled. Check credentials.")
        return None

    try:
        result = await service.create_verification(
            service="google", area_code="213", capability="sms"
        )

        print(f"✅ SMS Verification Created")
        print(f"   Verification ID: {result['id']}")
        print(f"   Phone Number: {result['phone_number']}")
        print(f"   Requested Area Code: {result['requested_area_code']}")
        print(f"   Assigned Area Code: {result['assigned_area_code']}")
        print(f"   Area Code Matched: {result['area_code_matched']}")
        print(f"   Cost: ${result['cost']}")

        # Cancel immediately to avoid charges
        await service.cancel_verification(result["id"])
        print(f"   ✅ Cancelled to avoid charges")

        return result

    except Exception as e:
        print(f"❌ SMS Test Failed: {e}")
        return None


async def test_voice_with_area_code():
    """Test voice verification with area code - THIS IS WHAT WE NEED TO VERIFY"""
    print("\n" + "=" * 80)
    print("TEST 2: Voice Verification with Area Code (CRITICAL TEST)")
    print("=" * 80)

    service = TextVerifiedService()

    if not service.enabled:
        print("❌ TextVerified service not enabled. Check credentials.")
        return None

    try:
        result = await service.create_verification(
            service="google", area_code="213", capability="voice"  # ← VOICE MODE
        )

        print(f"✅ Voice Verification Created")
        print(f"   Verification ID: {result['id']}")
        print(f"   Phone Number: {result['phone_number']}")
        print(f"   Requested Area Code: {result['requested_area_code']}")
        print(f"   Assigned Area Code: {result['assigned_area_code']}")
        print(f"   Area Code Matched: {result['area_code_matched']}")
        print(f"   Cost: ${result['cost']}")

        # CRITICAL: Check if area code was honored
        if result["area_code_matched"]:
            print(f"   ✅ AREA CODE HONORED - Voice supports area codes!")
        else:
            print(f"   ❌ AREA CODE NOT HONORED - Voice does NOT support area codes!")
            print(f"      Requested: {result['requested_area_code']}")
            print(f"      Got: {result['assigned_area_code']}")

        # Cancel immediately to avoid charges
        await service.cancel_verification(result["id"])
        print(f"   ✅ Cancelled to avoid charges")

        return result

    except Exception as e:
        print(f"❌ Voice Test Failed: {e}")
        import traceback

        traceback.print_exc()
        return None


async def test_voice_without_area_code():
    """Test voice verification without area code"""
    print("\n" + "=" * 80)
    print("TEST 3: Voice Verification WITHOUT Area Code")
    print("=" * 80)

    service = TextVerifiedService()

    if not service.enabled:
        print("❌ TextVerified service not enabled. Check credentials.")
        return None

    try:
        result = await service.create_verification(
            service="google", area_code=None, capability="voice"  # No area code
        )

        print(f"✅ Voice Verification Created (No Area Code)")
        print(f"   Verification ID: {result['id']}")
        print(f"   Phone Number: {result['phone_number']}")
        print(f"   Assigned Area Code: {result['assigned_area_code']}")
        print(f"   Cost: ${result['cost']}")

        # Cancel immediately to avoid charges
        await service.cancel_verification(result["id"])
        print(f"   ✅ Cancelled to avoid charges")

        return result

    except Exception as e:
        print(f"❌ Voice Test (No Area Code) Failed: {e}")
        return None


async def test_rental_with_area_code():
    """Test rental/reservation with area code - CHECK IF SUPPORTED"""
    print("\n" + "=" * 80)
    print("TEST 4: Rental with Area Code (Check if Supported)")
    print("=" * 80)

    service = TextVerifiedService()

    if not service.enabled:
        print("❌ TextVerified service not enabled. Check credentials.")
        return None

    # First, check if the method signature supports area_code
    import inspect

    sig = inspect.signature(service.create_reservation)
    params = list(sig.parameters.keys())

    print(f"   create_reservation() parameters: {params}")

    if "area_code" not in params:
        print(f"   ❌ area_code parameter NOT in method signature")
        print(f"   ℹ️  Current implementation does NOT support area codes for rentals")
        return None

    try:
        result = await service.create_reservation(
            service="google",
            area_code="213",  # Try to pass area code
            duration_hours=1.0,  # 1 hour rental
        )

        print(f"✅ Rental Created")
        print(f"   Reservation ID: {result['id']}")
        print(f"   Phone Number: {result['phone_number']}")
        print(f"   Cost: ${result['cost']}")

        # Check if area code was honored
        assigned_area_code = (
            result["phone_number"][2:5]
            if result["phone_number"].startswith("+1")
            else None
        )
        print(f"   Assigned Area Code: {assigned_area_code}")

        if assigned_area_code == "213":
            print(f"   ✅ AREA CODE HONORED - Rentals support area codes!")
        else:
            print(f"   ❌ AREA CODE NOT HONORED - Rentals do NOT support area codes!")

        return result

    except TypeError as e:
        print(f"   ❌ TypeError: {e}")
        print(f"   ℹ️  area_code parameter not supported by API")
        return None
    except Exception as e:
        print(f"❌ Rental Test Failed: {e}")
        return None


async def test_multiple_voice_area_codes():
    """Test voice with multiple different area codes to measure success rate"""
    print("\n" + "=" * 80)
    print("TEST 5: Voice with Multiple Area Codes (Success Rate)")
    print("=" * 80)

    service = TextVerifiedService()

    if not service.enabled:
        print("❌ TextVerified service not enabled. Check credentials.")
        return []

    test_area_codes = ["213", "310", "415", "646", "212"]
    results = []

    for area_code in test_area_codes:
        try:
            print(f"\n   Testing area code {area_code}...")
            result = await service.create_verification(
                service="google", area_code=area_code, capability="voice"
            )

            matched = result["area_code_matched"]
            assigned = result["assigned_area_code"]

            results.append(
                {"requested": area_code, "assigned": assigned, "matched": matched}
            )

            print(f"   Requested: {area_code}, Got: {assigned}, Match: {matched}")

            # Cancel immediately
            await service.cancel_verification(result["id"])

            # Small delay to avoid rate limiting
            await asyncio.sleep(2)

        except Exception as e:
            print(f"   ❌ Failed for {area_code}: {e}")
            results.append(
                {
                    "requested": area_code,
                    "assigned": None,
                    "matched": False,
                    "error": str(e),
                }
            )

    # Calculate success rate
    total = len(results)
    matched = sum(1 for r in results if r.get("matched", False))
    success_rate = (matched / total * 100) if total > 0 else 0

    print(f"\n   Success Rate: {matched}/{total} = {success_rate:.1f}%")

    if success_rate >= 80:
        print(f"   ✅ SUCCESS RATE ACCEPTABLE (>80%)")
    else:
        print(f"   ⚠️  SUCCESS RATE LOW (<80%)")

    return results


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("TextVerified Area Code Support Verification")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Purpose: Verify area code support for voice verification and rentals")
    print("=" * 80)

    # Check if credentials are set
    api_key = os.getenv("TEXTVERIFIED_API_KEY")
    api_username = os.getenv("TEXTVERIFIED_USERNAME") or os.getenv("TEXTVERIFIED_EMAIL")

    if not api_key or not api_username:
        print("\n❌ ERROR: TextVerified credentials not set!")
        print(
            "   Set TEXTVERIFIED_API_KEY and TEXTVERIFIED_USERNAME environment variables"
        )
        return

    print(f"\n✅ Credentials found")
    print(f"   API Key: {api_key[:10]}...")
    print(f"   Username: {api_username}")

    # Run tests
    sms_result = await test_sms_with_area_code()
    voice_result = await test_voice_with_area_code()
    voice_no_ac_result = await test_voice_without_area_code()
    rental_result = await test_rental_with_area_code()

    # Only run multiple tests if first voice test succeeded
    if voice_result:
        multiple_results = await test_multiple_voice_area_codes()
    else:
        multiple_results = []

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print("\n1. SMS Verification + Area Code:")
    if sms_result and sms_result.get("area_code_matched"):
        print("   ✅ CONFIRMED - Area codes work for SMS")
    else:
        print("   ⚠️  UNEXPECTED - SMS should support area codes")

    print("\n2. Voice Verification + Area Code:")
    if voice_result:
        if voice_result.get("area_code_matched"):
            print("   ✅ CONFIRMED - Area codes work for VOICE")
            print("   ℹ️  Voice verification UI can keep area code option")
        else:
            print("   ❌ NOT SUPPORTED - Area codes do NOT work for VOICE")
            print("   ⚠️  CRITICAL: Remove area code option from voice UI")
    else:
        print("   ❌ TEST FAILED - Could not verify")

    print("\n3. Voice Verification WITHOUT Area Code:")
    if voice_no_ac_result:
        print("   ✅ WORKS - Voice verification works without area code")
    else:
        print("   ❌ FAILED - Voice verification failed")

    print("\n4. Rentals + Area Code:")
    if rental_result:
        print("   ✅ SUPPORTED - Rentals support area codes")
        print("   ℹ️  Consider adding area code option to rentals UI")
    else:
        print("   ❌ NOT SUPPORTED - Rentals do NOT support area codes")
        print("   ℹ️  Current implementation is correct (no area code option)")

    if multiple_results:
        matched = sum(1 for r in multiple_results if r.get("matched", False))
        total = len(multiple_results)
        success_rate = (matched / total * 100) if total > 0 else 0
        print(f"\n5. Voice Area Code Success Rate:")
        print(f"   {matched}/{total} = {success_rate:.1f}%")
        if success_rate >= 80:
            print(f"   ✅ ACCEPTABLE - Can deploy with area code option")
        else:
            print(f"   ⚠️  LOW - Consider removing area code option")

    # Final recommendation
    print("\n" + "=" * 80)
    print("FINAL RECOMMENDATION")
    print("=" * 80)

    if voice_result and voice_result.get("area_code_matched"):
        print("\n✅ DEPLOY VOICE UI WITH AREA CODE OPTION")
        print("   - Area codes are honored for voice verification")
        print("   - UI implementation is correct")
        print("   - Monitor success rate in production")
    else:
        print("\n❌ DO NOT DEPLOY VOICE UI WITH AREA CODE OPTION")
        print("   - Area codes are NOT honored for voice verification")
        print("   - Remove area code option from voice UI")
        print("   - Update documentation to reflect SMS-only support")

    if not rental_result:
        print("\n✅ RENTALS IMPLEMENTATION IS CORRECT")
        print("   - No area code option (as expected)")
        print("   - No changes needed")

    print("\n" + "=" * 80)
    print("Test completed at: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
