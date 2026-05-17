#!/usr/bin/env python3
"""Check actual TextVerified pricing to inform platform pricing strategy."""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.textverified_service import TextVerifiedService


async def main():
    print("🔍 Checking TextVerified Pricing...\n")

    svc = TextVerifiedService()

    if not svc.enabled:
        print("❌ TextVerified not configured")
        print("Set TEXTVERIFIED_API_KEY and TEXTVERIFIED_EMAIL")
        sys.exit(1)

    try:
        services = await svc.get_services_list()

        if not services:
            print("❌ No services returned")
            sys.exit(1)

        print(f"✅ Found {len(services)} services\n")

        # Extract prices
        prices = [s["price"] for s in services if s.get("price") is not None]

        if not prices:
            print("⚠️  No pricing data available")
            sys.exit(1)

        # Calculate statistics
        avg = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        median = sorted(prices)[len(prices) // 2]

        print("📊 TextVerified Cost Analysis")
        print("=" * 50)
        print(f"Average:  ${avg:.2f}")
        print(f"Median:   ${median:.2f}")
        print(f"Min:      ${min_price:.2f}")
        print(f"Max:      ${max_price:.2f}")
        print(f"Services: {len(prices)} priced")

        # Pricing recommendations
        print("\n💡 Platform Pricing Recommendations")
        print("=" * 50)

        # 36% margin (sustainable)
        rec_36 = avg * 1.57
        profit_36 = rec_36 - avg
        print(f"Conservative (36% margin): ${rec_36:.2f}")
        print(f"  → Profit: ${profit_36:.2f} per SMS")
        print(f"  → Per 1000: ${profit_36 * 1000:.0f}")

        # 50% margin (aggressive)
        rec_50 = avg * 2.0
        profit_50 = rec_50 - avg
        print(f"\nAggressive (50% margin):   ${rec_50:.2f}")
        print(f"  → Profit: ${profit_50:.2f} per SMS")
        print(f"  → Per 1000: ${profit_50 * 1000:.0f}")

        # Current pricing analysis
        current = 2.12
        current_profit = current - avg
        current_margin = (current_profit / current) * 100 if current > 0 else 0

        print(f"\n⚠️  Current Platform Price: ${current:.2f}")
        print(f"  → Profit: ${current_profit:.2f} per SMS")
        print(f"  → Margin: {current_margin:.1f}%")
        if current_profit < 0.40:
            print(f"  → Status: ❌ UNSUSTAINABLE (need $0.40+ profit)")

        # Top services
        print("\n📋 Top 10 Services by Price")
        print("=" * 50)
        sorted_services = sorted(
            [s for s in services if s.get("price")],
            key=lambda x: x["price"],
            reverse=True,
        )
        for s in sorted_services[:10]:
            print(f"  {s['name']:<30} ${s['price']:.2f}")

        # Bottom services
        print("\n📋 Cheapest 10 Services")
        print("=" * 50)
        for s in sorted_services[-10:]:
            print(f"  {s['name']:<30} ${s['price']:.2f}")

        print("\n" + "=" * 50)
        print("✅ Analysis Complete")
        print("\nNext Steps:")
        print("1. Review recommendations above")
        print("2. Update tier_config.py with new pricing")
        print("3. Run migration script")
        print("4. Deploy to production")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
