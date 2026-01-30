#!/usr/bin/env python3
"""Check SMS, cancel verification, and verify refund."""

import asyncio
import sys

sys.path.insert(0, "/Users/machine/Desktop/Namaskah. app")

from app.services.textverified_service import TextVerifiedService


async def check_cancel_verify():
    verification_id = "lr_01KFG7NPSZATBWG3DM9GSNRF5Z"

    tv_service = TextVerifiedService()

    print("=" * 60)
    print("Step 1: Check for SMS Code")
    print("=" * 60)

    # Get balance before
    balance_before = await tv_service.get_balance()
    print(f"💰 Balance BEFORE: ${balance_before['balance']:.2f}")

    # Check for SMS one more time
    status = await tv_service.check_sms(verification_id)
    print(f"📨 SMS Status: {status['status']}")
    if status["sms_code"]:
        print(f"✅ Code: {status['sms_code']}")
    else:
        print("❌ No code received")

    print("\n" + "=" * 60)
    print("Step 2: Cancel Verification")
    print("=" * 60)

    # Cancel the verification
    cancelled = await tv_service.cancel_activation(verification_id)
    if cancelled:
        print("✅ Verification cancelled successfully")
    else:
        print("❌ Cancellation failed")

    # Wait a moment for refund to process
    print("\n⏳ Waiting 3 seconds for refund to process...")
    await asyncio.sleep(3)

    print("\n" + "=" * 60)
    print("Step 3: Verify Refund")
    print("=" * 60)

    # Get balance after
    balance_after = await tv_service.get_balance()
    print(f"💰 Balance AFTER: ${balance_after['balance']:.2f}")

    # Calculate difference
    refund = balance_after["balance"] - balance_before["balance"]
    print(f"\n{'✅' if refund > 0 else '❌'} Refund Amount: ${refund:.2f}")

    if refund > 0:
        print(f"✅ CONFIRMED: ${refund:.2f} refunded to account")
    else:
        print("⚠️  No refund detected (may take longer to process)")


if __name__ == "__main__":
    asyncio.run(check_cancel_verify())
