#!/usr/bin/env python3
"""Test script to purchase 704 Charlotte number and retrieve SMS code."""

import asyncio
import sys
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.insert(0, "/Users/machine/Desktop/Namaskah. app")

from app.core.database import get_db
from app.models.user import User
from app.services.textverified_service import TextVerifiedService


async def test_704_charlotte():
    """Purchase 704 Charlotte number and wait for SMS."""

    print("=" * 60)
    print("Testing 704 Charlotte Number Purchase")
    print("=" * 60)

    # Initialize TextVerified service
    tv_service = TextVerifiedService()

    if not tv_service.enabled:
        print("❌ TextVerified service not enabled")
        print("Check TEXTVERIFIED_API_KEY and TEXTVERIFIED_EMAIL in .env")
        return

    print("✅ TextVerified service initialized")

    # Check balance
    try:
        balance_data = await tv_service.get_balance()
        print(f"💰 Account Balance: ${balance_data['balance']:.2f}")

        if balance_data["balance"] < 2.0:
            print("❌ Insufficient balance (need at least $2.00)")
            return
    except Exception as e:
        print(f"❌ Failed to get balance: {e}")
        return

    # Purchase number with 704 area code
    print("\n📞 Purchasing 704 Charlotte number for telegram...")
    try:
        result = await tv_service.create_verification(
            service="telegram", area_code="704"
        )

        print(f"✅ Number purchased!")
        print(f"   Phone: {result['phone_number']}")
        print(f"   ID: {result['id']}")
        print(f"   Cost: ${result['cost']:.2f}")

        verification_id = result["id"]

    except Exception as e:
        print(f"❌ Purchase failed: {e}")
        return

    # Poll for SMS code
    print(f"\n📨 Waiting for SMS code (max 2 minutes)...")
    max_attempts = 24  # 2 minutes (5 sec intervals)

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

    print(f"\n⏱️  Timeout - No SMS received after {max_attempts * 5} seconds")
    print(f"   You can check manually with verification ID: {verification_id}")


if __name__ == "__main__":
    asyncio.run(test_704_charlotte())
