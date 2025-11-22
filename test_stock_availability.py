#!/usr/bin/env python3
"""Test which services have available numbers in stock."""
import textverified
from textverified.data import ReservationCapability
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("TEXTVERIFIED_API_KEY")
email = os.getenv("TEXTVERIFIED_EMAIL")

client = textverified.TextVerified(api_key=api_key, api_username=email)

print("=" * 60)
print("CHECKING SERVICE AVAILABILITY")
print("=" * 60)

services = ["telegram", "whatsapp", "discord", "instagram", "tiktok", "twitter", "facebook", "gmail", "viber", "signal"]

for service in services:
    try:
        verification = client.verifications.create(
            service_name=service,
            capability=ReservationCapability.SMS
        )
        print(f"✅ {service.upper()}: SUCCESS - {verification.number}")
        print(f"   Cost: ${verification.total_cost}, ID: {verification.id}")
        break
    except Exception as e:
        error_msg = str(e)
        if "out of stock" in error_msg.lower() or "unavailable" in error_msg.lower():
            print(f"❌ {service.upper()}: OUT OF STOCK")
        else:
            print(f"⚠️  {service.upper()}: {error_msg[:60]}")

print("\n" + "=" * 60)
