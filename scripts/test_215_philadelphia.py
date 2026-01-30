#!/usr/bin/env python3
"""Test script to purchase 215 Philadelphia number and retrieve SMS code."""

import asyncio
import sys

sys.path.insert(0, "/Users/machine/Desktop/Namaskah. app")

from app.services.textverified_service import TextVerifiedService


async def test_215_philadelphia():
    """Purchase 215 Philadelphia number and wait for SMS."""

    print("=" * 60)
    print("Testing 215 Philadelphia Number Purchase")
    print("=" * 60)

    tv_service = TextVerifiedService()

    if not tv_service.enabled:
        print("❌ TextVerified service not enabled")
        return

    print("✅ TextVerified service initialized")

    balance_data = await tv_service.get_balance()
    print(f"💰 Account Balance: ${balance_data['balance']:.2f}")

    print("\n📞 Purchasing 215 Philadelphia number for telegram...")
    try:
        result = await tv_service.create_verification(
            service="telegram", area_code="215"
        )

        print(f"✅ Number purchased!")
        print(f"   Phone: {result['phone_number']}")
        print(f"   ID: {result['id']}")
        print(f"   Cost: ${result['cost']:.2f}")

        verification_id = result["id"]

    except Exception as e:
        print(f"❌ Purchase failed: {e}")
        return

    print(f"\n📨 Waiting for SMS code (max 2 minutes)...")
    max_attempts = 24

    for attempt in range(1, max_attempts + 1):
        try:
            status = await tv_service.check_sms(verification_id)

            if status["status"] == "received" and status["sms_code"]:
                print(f"\n✅ SMS CODE RECEIVED!")
                print(f"   Code: {status['sms_code']}")
                print(f"   Full Text: {status['sms_text']}")
                return

            print(
                f"   Attempt {attempt}/{max_attempts} - Status: {status['status']}",
                end="\r",
            )
            await asyncio.sleep(5)

        except Exception as e:
            print(f"\n❌ Error checking SMS: {e}")
            break

    print(f"\n⏱️  Timeout - No SMS received")


if __name__ == "__main__":
    asyncio.run(test_215_philadelphia())
