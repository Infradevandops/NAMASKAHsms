#!/usr/bin/env python3
"""Check detailed verification status."""


import asyncio
import sys
from app.services.textverified_service import TextVerifiedService

sys.path.insert(0, "/Users/machine/Desktop/Namaskah. app")


async def check_status():
    verification_id = "lr_01KFG7NPSZATBWG3DM9GSNRF5Z"

    tv_service = TextVerifiedService()

    print("Checking verification details...")

try:
        details = tv_service.client.verifications.details(verification_id)
        print(f"\nVerification ID: {details.id}")
        print(f"Number: {details.number}")
        print(f"Service: {details.service_name}")
        print(f"State: {details.state}")
        print(f"Cost: ${details.total_cost:.2f}")
        print(f"Created: {details.created_at}")
        print(f"Ends: {details.ends_at}")
        print(f"\nCan Cancel: {details.cancel.can_cancel}")
        print(f"Can Reactivate: {details.reactivate.can_reactivate}")

        # Check balance
        balance = await tv_service.get_balance()
        print(f"\n💰 Current Balance: ${balance['balance']:.2f}")

except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(check_status())
