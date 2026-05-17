#!/usr/bin/env python3
"""Compare pricing across all SMS providers: TextVerified, 5sim, PVAPins, Telnyx."""

import asyncio
import csv
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.providers.fivesim_adapter import FiveSimAdapter
from app.services.providers.pvapins_adapter import PVAPinsAdapter
from app.services.providers.telnyx_adapter import TelnyxAdapter
from app.services.textverified_service import TextVerifiedService

# Popular services to check across all providers
POPULAR_SERVICES = [
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


async def check_textverified_pricing():
    """Get TextVerified pricing for popular services."""
    print("\n🔍 Checking TextVerified Pricing...")

    svc = TextVerifiedService()
    if not svc.enabled:
        print("  ❌ Not configured")
        return {}

    prices = {}
    for service in POPULAR_SERVICES:
        try:
            from textverified.data import NumberType, ReservationCapability

            snap = await asyncio.wait_for(
                asyncio.to_thread(
                    svc.client.verifications.pricing,
                    service_name=service,
                    area_code=False,
                    carrier=False,
                    number_type=NumberType.MOBILE,
                    capability=ReservationCapability.SMS,
                ),
                timeout=10.0,
            )
            prices[service] = float(snap.price)
            print(f"  ✅ {service:<15} ${prices[service]:.2f}")
        except Exception as e:
            print(f"  ⚠️  {service:<15} Error: {str(e)[:50]}")
        await asyncio.sleep(0.3)

    return prices


async def check_fivesim_pricing():
    """Get 5sim pricing for popular services."""
    print("\n🔍 Checking 5sim Pricing...")

    adapter = FiveSimAdapter()
    if not adapter.enabled:
        print("  ❌ Not configured")
        return {}

    prices = {}

    # 5sim requires country - use USA as baseline
    country = "usa"

    for service in POPULAR_SERVICES:
        try:
            service_name = await adapter._map_service(service)

            # Get product prices
            response = await adapter.client.get(
                f"{adapter.base_url}/guest/products/{country}/{service_name}"
            )
            response.raise_for_status()
            data = response.json()

            # Find cheapest operator
            min_price = float("inf")
            for operator, operator_data in data.items():
                if isinstance(operator_data, dict):
                    price = operator_data.get("cost", float("inf"))
                    count = operator_data.get("count", 0)
                    if count > 0 and price < min_price:
                        min_price = price

            if min_price != float("inf"):
                prices[service] = min_price
                print(f"  ✅ {service:<15} ${prices[service]:.2f}")
            else:
                print(f"  ⚠️  {service:<15} No inventory")

        except Exception as e:
            print(f"  ⚠️  {service:<15} Error: {str(e)[:50]}")
        await asyncio.sleep(0.3)

    return prices


async def check_pvapins_pricing():
    """Get PVAPins pricing estimate."""
    print("\n🔍 Checking PVAPins Pricing...")

    adapter = PVAPinsAdapter()
    if not adapter.enabled:
        print("  ❌ Not configured")
        return {}

    # PVAPins doesn't expose pricing API - use industry estimates
    print("  ℹ️  PVAPins doesn't expose pricing API")
    print("  ℹ️  Using industry estimates for Southeast Asia:")

    # Typical PVAPins pricing (based on market research)
    estimates = {
        "google": 0.80,
        "facebook": 0.75,
        "whatsapp": 1.20,
        "telegram": 0.90,
        "instagram": 0.70,
        "twitter": 0.65,
        "tiktok": 0.85,
        "discord": 0.75,
        "uber": 0.70,
        "amazon": 0.80,
        "microsoft": 0.75,
        "yahoo": 0.65,
        "linkedin": 0.70,
        "snapchat": 0.60,
        "netflix": 0.80,
    }

    for service, price in estimates.items():
        print(f"  📊 {service:<15} ~${price:.2f} (estimate)")

    return estimates


async def check_telnyx_pricing():
    """Get Telnyx pricing estimate."""
    print("\n🔍 Checking Telnyx Pricing...")

    adapter = TelnyxAdapter()
    if not adapter.enabled:
        print("  ❌ Not configured")
        return {}

    # Telnyx pricing is based on number rental + SMS costs
    print("  ℹ️  Telnyx uses rental model:")
    print("  ℹ️  Number rental: ~$1.00/month")
    print("  ℹ️  SMS cost: ~$0.01-0.05 per message")
    print("  ℹ️  Effective cost per verification: ~$1.50-2.50")

    # Estimated effective cost per verification
    estimates = {service: 2.00 for service in POPULAR_SERVICES}

    for service in POPULAR_SERVICES:
        print(f"  📊 {service:<15} ~${estimates[service]:.2f} (estimate)")

    return estimates


def calculate_statistics(prices):
    """Calculate pricing statistics."""
    if not prices:
        return None

    values = list(prices.values())
    return {
        "avg": sum(values) / len(values),
        "min": min(values),
        "max": max(values),
        "count": len(values),
    }


def generate_csv_report(all_prices, output_file):
    """Generate CSV report with all provider pricing."""
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)

        # Header
        writer.writerow(
            [
                "Service",
                "TextVerified ($)",
                "5sim ($)",
                "PVAPins ($)",
                "Telnyx ($)",
                "Cheapest",
                "Most Expensive",
                "Average",
            ]
        )

        # Data rows
        for service in POPULAR_SERVICES:
            tv = all_prices["textverified"].get(service, "N/A")
            fs = all_prices["fivesim"].get(service, "N/A")
            pv = all_prices["pvapins"].get(service, "N/A")
            tx = all_prices["telnyx"].get(service, "N/A")

            # Calculate row statistics
            row_prices = []
            for p in [tv, fs, pv, tx]:
                if isinstance(p, (int, float)):
                    row_prices.append(p)

            if row_prices:
                cheapest = min(row_prices)
                most_exp = max(row_prices)
                average = sum(row_prices) / len(row_prices)
            else:
                cheapest = most_exp = average = "N/A"

            writer.writerow(
                [
                    service,
                    f"{tv:.2f}" if isinstance(tv, (int, float)) else tv,
                    f"{fs:.2f}" if isinstance(fs, (int, float)) else fs,
                    f"{pv:.2f}" if isinstance(pv, (int, float)) else pv,
                    f"{tx:.2f}" if isinstance(tx, (int, float)) else tx,
                    (
                        f"{cheapest:.2f}"
                        if isinstance(cheapest, (int, float))
                        else cheapest
                    ),
                    (
                        f"{most_exp:.2f}"
                        if isinstance(most_exp, (int, float))
                        else most_exp
                    ),
                    f"{average:.2f}" if isinstance(average, (int, float)) else average,
                ]
            )

        # Summary row
        writer.writerow([])
        writer.writerow(["SUMMARY"])

        for provider, prices in all_prices.items():
            stats = calculate_statistics(prices)
            if stats:
                writer.writerow(
                    [
                        f"{provider.upper()} Average",
                        f"${stats['avg']:.2f}",
                        f"Min: ${stats['min']:.2f}",
                        f"Max: ${stats['max']:.2f}",
                        f"Services: {stats['count']}",
                    ]
                )


async def main():
    print("=" * 70)
    print("SMS PROVIDER PRICING COMPARISON")
    print("=" * 70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Services checked: {len(POPULAR_SERVICES)}")

    # Check all providers
    all_prices = {
        "textverified": await check_textverified_pricing(),
        "fivesim": await check_fivesim_pricing(),
        "pvapins": await check_pvapins_pricing(),
        "telnyx": await check_telnyx_pricing(),
    }

    # Calculate statistics
    print("\n" + "=" * 70)
    print("PROVIDER STATISTICS")
    print("=" * 70)

    for provider, prices in all_prices.items():
        stats = calculate_statistics(prices)
        if stats:
            print(f"\n{provider.upper()}:")
            print(f"  Average: ${stats['avg']:.2f}")
            print(f"  Range:   ${stats['min']:.2f} - ${stats['max']:.2f}")
            print(f"  Services: {stats['count']}")

    # Overall comparison
    print("\n" + "=" * 70)
    print("OVERALL COMPARISON")
    print("=" * 70)

    all_averages = {
        provider: calculate_statistics(prices)["avg"]
        for provider, prices in all_prices.items()
        if calculate_statistics(prices)
    }

    if all_averages:
        cheapest_provider = min(all_averages, key=all_averages.get)
        most_exp_provider = max(all_averages, key=all_averages.get)

        print(
            f"\nCheapest Provider:     {cheapest_provider.upper()} (${all_averages[cheapest_provider]:.2f} avg)"
        )
        print(
            f"Most Expensive:        {most_exp_provider.upper()} (${all_averages[most_exp_provider]:.2f} avg)"
        )
        print(
            f"Overall Average:       ${sum(all_averages.values()) / len(all_averages):.2f}"
        )

    # Platform pricing recommendations
    print("\n" + "=" * 70)
    print("PLATFORM PRICING RECOMMENDATIONS")
    print("=" * 70)

    if all_averages:
        avg_provider_cost = sum(all_averages.values()) / len(all_averages)

        # Calculate recommended pricing
        fees = 0.41  # Payment + Failures + Refunds + Operating

        scenarios = [
            ("Conservative (30% margin)", avg_provider_cost * 1.43),
            ("Recommended (50% margin)", avg_provider_cost * 2.00),
            ("Aggressive (70% margin)", avg_provider_cost * 3.33),
        ]

        for name, price in scenarios:
            gross_profit = price - avg_provider_cost
            net_profit = gross_profit - fees
            margin = (net_profit / price) * 100

            print(f"\n{name}: ${price:.2f}/SMS")
            print(f"  Provider Cost: ${avg_provider_cost:.2f}")
            print(f"  Gross Profit:  ${gross_profit:.2f}")
            print(f"  Fees/Costs:    ${fees:.2f}")
            print(f"  NET PROFIT:    ${net_profit:.2f}")
            print(f"  Net Margin:    {margin:.1f}%")
            print(f"  Per 1000 SMS:  ${net_profit * 1000:.0f}")

    # Generate CSV report
    output_file = "docs/analysis/provider_pricing_comparison.csv"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    generate_csv_report(all_prices, output_file)

    print("\n" + "=" * 70)
    print(f"✅ CSV Report saved to: {output_file}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
