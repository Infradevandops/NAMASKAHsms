#!/usr/bin/env python3
"""Check TextVerified pricing for popular services."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.textverified_service import TextVerifiedService


async def check_service_price(svc, service_name):
    """Get price for a specific service."""
    try:
        # Use the pricing method directly
        from textverified.data import NumberType, ReservationCapability

        snap = await asyncio.wait_for(
            asyncio.to_thread(
                svc.client.verifications.pricing,
                service_name=service_name,
                area_code=False,
                carrier=False,
                number_type=NumberType.MOBILE,
                capability=ReservationCapability.SMS,
            ),
            timeout=10.0,
        )
        return float(snap.price)
    except Exception as e:
        print(f"  ⚠️  {service_name}: Error - {e}")
        return None


async def main():
    print("🔍 Checking TextVerified Pricing for Popular Services...\n")

    svc = TextVerifiedService()

    if not svc.enabled:
        print("❌ TextVerified not configured")
        sys.exit(1)

    # Popular services to check
    popular_services = [
        "google",
        "facebook",
        "whatsapp",
        "telegram",
        "instagram",
        "twitter",
        "tiktok",
        "discord",
        "uber",
        "amazon",
        "microsoft",
        "yahoo",
        "linkedin",
        "snapchat",
        "netflix",
    ]

    print("📊 Checking prices for popular services...\n")

    prices = []
    for service in popular_services:
        price = await check_service_price(svc, service)
        if price:
            prices.append(price)
            print(f"  ✅ {service:<15} ${price:.2f}")
        await asyncio.sleep(0.5)  # Rate limit

    if not prices:
        print("\n❌ Could not fetch any prices")
        sys.exit(1)

    # Calculate statistics
    avg = sum(prices) / len(prices)
    min_price = min(prices)
    max_price = max(prices)

    print("\n" + "=" * 60)
    print("📊 TextVerified Cost Analysis")
    print("=" * 60)
    print(f"Average Cost:  ${avg:.2f}")
    print(f"Min Cost:      ${min_price:.2f}")
    print(f"Max Cost:      ${max_price:.2f}")
    print(f"Services:      {len(prices)}")

    # Pricing recommendations
    print("\n" + "=" * 60)
    print("💡 Platform Pricing Recommendations")
    print("=" * 60)

    # Current pricing
    current = 2.12
    current_profit = current - avg
    current_margin = (current_profit / current) * 100

    print(f"\n⚠️  CURRENT: ${current:.2f}/SMS")
    print(f"   Provider Cost: ${avg:.2f}")
    print(f"   Gross Profit:  ${current_profit:.2f}")
    print(f"   Margin:        {current_margin:.1f}%")

    # After fees and costs
    fees = 0.09 + 0.18 + 0.04 + 0.10  # Payment + Failures + Refunds + Operating
    net_profit = current_profit - fees
    print(f"   Fees/Costs:    ${fees:.2f}")
    print(f"   NET PROFIT:    ${net_profit:.2f}")
    if net_profit < 0:
        print(f"   Status:        ❌ LOSING ${abs(net_profit):.2f} per SMS")
    else:
        print(f"   Status:        ✅ Profit ${net_profit:.2f} per SMS")

    # Recommended: $2.75
    rec_275 = 2.75
    rec_275_profit = rec_275 - avg
    rec_275_margin = (rec_275_profit / rec_275) * 100
    rec_275_net = rec_275_profit - fees

    print(f"\n✅ RECOMMENDED: ${rec_275:.2f}/SMS")
    print(f"   Provider Cost: ${avg:.2f}")
    print(f"   Gross Profit:  ${rec_275_profit:.2f}")
    print(f"   Margin:        {rec_275_margin:.1f}%")
    print(f"   Fees/Costs:    ${fees:.2f}")
    print(f"   NET PROFIT:    ${rec_275_net:.2f}")
    print(f"   Per 1000 SMS:  ${rec_275_net * 1000:.0f}")

    # Aggressive: $3.50
    rec_350 = 3.50
    rec_350_profit = rec_350 - avg
    rec_350_margin = (rec_350_profit / rec_350) * 100
    rec_350_net = rec_350_profit - fees

    print(f"\n💰 AGGRESSIVE: ${rec_350:.2f}/SMS")
    print(f"   Provider Cost: ${avg:.2f}")
    print(f"   Gross Profit:  ${rec_350_profit:.2f}")
    print(f"   Margin:        {rec_350_margin:.1f}%")
    print(f"   Fees/Costs:    ${fees:.2f}")
    print(f"   NET PROFIT:    ${rec_350_net:.2f}")
    print(f"   Per 1000 SMS:  ${rec_350_net * 1000:.0f}")

    print("\n" + "=" * 60)
    print("✅ Analysis Complete")
    print("\nNext Steps:")
    print("1. Update tier_config.py to $2.75 (minimum)")
    print("2. Consider $3.50 for better margins")
    print("3. Run migration script")
    print("4. Deploy to production")


if __name__ == "__main__":
    asyncio.run(main())
