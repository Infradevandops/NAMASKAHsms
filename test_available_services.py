#!/usr/bin/env python3
"""Test available services and pricing from TextVerified."""
import textverified
from textverified.data import ReservationCapability, NumberType
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("TEXTVERIFIED_API_KEY")
email = os.getenv("TEXTVERIFIED_EMAIL")

client = textverified.TextVerified(api_key=api_key, api_username=email)

print("=" * 60)
print("TEXTVERIFIED AVAILABLE SERVICES & PRICING")
print("=" * 60)

# Get account balance
try:
    account = client.account.me()
    print(f"\n💰 Account Balance: ${account.current_balance}")
except Exception as e:
    print(f"❌ Balance error: {e}")

# Get services
print("\n📱 Available Services:")
try:
    services = client.services.list(
        number_type=NumberType.MOBILE,
        reservation_type="verification"
    )
    for i, service in enumerate(services[:10], 1):
        print(f"  {i}. {service.service_name}")
except Exception as e:
    print(f"❌ Services error: {e}")

# Check pricing for popular services
print("\n💵 Pricing for Popular Services:")
popular_services = ["telegram", "whatsapp", "discord", "instagram", "tiktok"]

for service in popular_services:
    try:
        pricing = client.verifications.pricing(
            service_name=service,
            area_code=False,
            carrier=False,
            number_type=NumberType.MOBILE,
            capability=ReservationCapability.SMS
        )
        print(f"  ✅ {service.upper()}: ${pricing.price}")
    except Exception as e:
        print(f"  ❌ {service.upper()}: {str(e)[:50]}")

print("\n" + "=" * 60)
