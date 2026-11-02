"""
Live purchasability probe — runs against real TextVerified API.
Usage (on server):
    docker compose exec app python scripts/test_purchasable.py
"""

import asyncio
import sys

sys.path.insert(0, "/app")

SERVICES_TO_PROBE = [
    "tinder",
    "google",
    "facebook",
    "instagram",
    "twitter",
    "whatsapp",
    "telegram",
    "discord",
    "snapchat",
    "uber",
    "lyft",
    "amazon",
    "microsoft",
    "apple",
    "paypal",
]


async def main():
    from app.services.textverified_service import TextVerifiedService

    svc = TextVerifiedService()
    if not svc.enabled:
        print("ERROR: TextVerifiedService is disabled — check credentials/proxy")
        return

    # 1. Balance check
    bal = await svc.get_balance()
    print(f"\nTV Balance: ${bal.get('balance', 0):.2f}")
    if bal.get("error"):
        print(f"  WARNING: {bal['error']}")

    # 2. Availability probe
    print(f"\nProbing {len(SERVICES_TO_PROBE)} services...\n")
    print(f"{'Service':<20} {'Available':<12} {'Price':<10} {'Reason'}")
    print("-" * 55)

    available, unavailable, rate_limited = [], [], []

    async def probe(name):
        result = await svc.check_service_available(name)
        return name, result

    results = await asyncio.gather(*[probe(s) for s in SERVICES_TO_PROBE])

    for name, r in sorted(results, key=lambda x: x[0]):
        avail = r.get("available")
        price = r.get("price")
        reason = r.get("reason", "")
        price_str = f"${price:.4f}" if price else "unknown"

        if avail and price is None and not reason:
            rate_limited.append(name)
            status = "⚠ rate-limit"
        elif avail:
            available.append(name)
            status = "✅ yes"
        else:
            unavailable.append(name)
            status = "❌ no"

        print(f"{name:<20} {status:<12} {price_str:<10} {reason}")

    print(
        f"\nSummary: {len(available)} available, {len(unavailable)} unavailable, {len(rate_limited)} rate-limited"
    )

    # 3. Attempt one real purchase on the cheapest available service
    if not available:
        print("\nNo services available for purchase test — skipping.")
        return

    target = available[0]
    print(f"\nAttempting real purchase: {target} ...")
    try:
        result = await svc.create_verification(service=target, max_retries=1)
        print(
            f"  ✅ Purchased: {result['phone_number']} (id={result['id']}, cost=${result['cost']})"
        )
        # Cancel immediately — this is a test
        cancelled = await svc.cancel_verification(result["id"])
        print(f"  Cancelled: {cancelled}")
    except Exception as e:
        print(f"  ❌ Purchase failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
