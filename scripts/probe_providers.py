#!/usr/bin/env python3
"""
Provider probe — tests all three providers and shows exactly what they return.
Run: python3 scripts/probe_providers.py
"""

import asyncio
import httpx
import json
import os
import sys

TELNYX_KEY = os.getenv("TELNYX_API_KEY", "")
FIVESIM_KEY = os.getenv("FIVESIM_API_KEY", "")

SEP = "=" * 60


def section(title):
    print(f"\n{SEP}\n{title}\n{SEP}")


def ok(label, value):
    print(f"  ✓  {label}: {value}")


def fail(label, value):
    print(f"  ✗  {label}: {value}")


def info(label, value):
    print(f"     {label}: {value}")


# ── TELNYX ────────────────────────────────────────────────────────────────────

async def probe_telnyx():
    section("TELNYX")
    headers = {
        "Authorization": f"Bearer {TELNYX_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=20) as client:

        # 1. Balance
        try:
            r = await client.get("https://api.telnyx.com/v2/balance", headers=headers)
            d = r.json()
            balance = d.get("data", {}).get("balance", "?")
            ok("Balance", f"${balance}")
        except Exception as e:
            fail("Balance", e)

        # 2. US number search (area code 415)
        try:
            r = await client.get(
                "https://api.telnyx.com/v2/available_phone_numbers",
                headers=headers,
                params={
                    "filter[country_code]": "US",
                    "filter[national_destination_code]": "415",
                    "filter[features]": "sms",
                    "filter[limit]": 3,
                },
            )
            d = r.json()
            numbers = d.get("data", [])
            if numbers:
                ok("US 415 search", f"{len(numbers)} numbers found")
                for n in numbers[:2]:
                    info("  number", n.get("phone_number"))
                    info("  cost", n.get("cost_information", {}).get("upfront_cost"))
                    info("  features", n.get("features", []))
            else:
                fail("US 415 search", "0 results")
        except Exception as e:
            fail("US 415 search", e)

        # 3. GB number search (country only)
        try:
            r = await client.get(
                "https://api.telnyx.com/v2/available_phone_numbers",
                headers=headers,
                params={
                    "filter[country_code]": "GB",
                    "filter[features]": "sms",
                    "filter[limit]": 3,
                },
            )
            d = r.json()
            numbers = d.get("data", [])
            if numbers:
                ok("GB country search", f"{len(numbers)} numbers found")
                for n in numbers[:2]:
                    info("  number", n.get("phone_number"))
                    info("  locality", n.get("locality"))
                    info("  region", n.get("administrative_area"))
            else:
                fail("GB country search", "0 results")
                info("  error", d.get("errors", "?"))
        except Exception as e:
            fail("GB country search", e)

        # 4. GB + locality=London
        try:
            r = await client.get(
                "https://api.telnyx.com/v2/available_phone_numbers",
                headers=headers,
                params={
                    "filter[country_code]": "GB",
                    "filter[locality]": "London",
                    "filter[features]": "sms",
                    "filter[limit]": 3,
                },
            )
            d = r.json()
            numbers = d.get("data", [])
            if numbers:
                ok("GB + city=London", f"{len(numbers)} numbers found")
                for n in numbers[:2]:
                    info("  number", n.get("phone_number"))
                    info("  locality", n.get("locality"))
            else:
                fail("GB + city=London", "0 results")
                info("  errors", d.get("errors", "?"))
        except Exception as e:
            fail("GB + city=London", e)

        # 5. DE number search
        try:
            r = await client.get(
                "https://api.telnyx.com/v2/available_phone_numbers",
                headers=headers,
                params={
                    "filter[country_code]": "DE",
                    "filter[features]": "sms",
                    "filter[limit]": 3,
                },
            )
            d = r.json()
            numbers = d.get("data", [])
            if numbers:
                ok("DE country search", f"{len(numbers)} numbers found")
                for n in numbers[:1]:
                    info("  number", n.get("phone_number"))
                    info("  locality", n.get("locality"))
            else:
                fail("DE country search", "0 results")
                info("  errors", d.get("errors", "?"))
        except Exception as e:
            fail("DE country search", e)


# ── 5SIM ──────────────────────────────────────────────────────────────────────

async def probe_fivesim():
    section("5SIM")
    headers = {
        "Authorization": f"Bearer {FIVESIM_KEY}",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=20) as client:

        # 1. Balance
        try:
            r = await client.get("https://5sim.net/v1/user/profile", headers=headers)
            d = r.json()
            balance = d.get("balance", "?")
            ok("Balance", f"${balance}")
            info("  rating", d.get("rating"))
        except Exception as e:
            fail("Balance", e)

        # 2. Available countries
        try:
            r = await client.get("https://5sim.net/v1/guest/countries", headers=headers)
            d = r.json()
            count = len(d) if isinstance(d, dict) else "?"
            ok("Countries available", count)
            sample = list(d.keys())[:5] if isinstance(d, dict) else []
            info("  sample", sample)
        except Exception as e:
            fail("Countries", e)

        # 3. GB + whatsapp products (shows operators + prices)
        try:
            r = await client.get(
                "https://5sim.net/v1/guest/products/unitedkingdom/whatsapp",
                headers=headers,
            )
            d = r.json()
            if isinstance(d, dict) and d:
                ok("GB whatsapp operators", f"{len(d)} operators")
                for op, data in list(d.items())[:3]:
                    info(f"  {op}", f"cost=${data.get('Cost', data.get('cost', '?'))} count={data.get('Count', data.get('count', '?'))}")
            else:
                fail("GB whatsapp operators", f"empty or error: {d}")
        except Exception as e:
            fail("GB whatsapp operators", e)

        # 4. DE + telegram products
        try:
            r = await client.get(
                "https://5sim.net/v1/guest/products/germany/telegram",
                headers=headers,
            )
            d = r.json()
            if isinstance(d, dict) and d:
                ok("DE telegram operators", f"{len(d)} operators")
                for op, data in list(d.items())[:3]:
                    info(f"  {op}", f"cost=${data.get('Cost', data.get('cost', '?'))} count={data.get('Count', data.get('count', '?'))}")
            else:
                fail("DE telegram operators", f"empty or error: {d}")
        except Exception as e:
            fail("DE telegram operators", e)

        # 5. US + google products
        try:
            r = await client.get(
                "https://5sim.net/v1/guest/products/usa/google",
                headers=headers,
            )
            d = r.json()
            if isinstance(d, dict) and d:
                ok("US google operators", f"{len(d)} operators")
                for op, data in list(d.items())[:3]:
                    info(f"  {op}", f"cost=${data.get('Cost', data.get('cost', '?'))} count={data.get('Count', data.get('count', '?'))}")
            else:
                fail("US google operators", f"empty or error: {d}")
        except Exception as e:
            fail("US google operators", e)


# ── TEXTVERIFIED ──────────────────────────────────────────────────────────────

async def probe_textverified():
    section("TEXTVERIFIED")
    try:
        import textverified
        from textverified.data import NumberType, ReservationType, ReservationCapability
    except ImportError:
        fail("Import", "textverified library not installed")
        return

    tv_key = os.getenv("TEXTVERIFIED_API_KEY")
    tv_email = os.getenv("TEXTVERIFIED_EMAIL") or os.getenv("TEXTVERIFIED_USERNAME")

    if not tv_key or not tv_email:
        fail("Credentials", "TEXTVERIFIED_API_KEY or TEXTVERIFIED_EMAIL not set in env")
        return

    try:
        client = textverified.TextVerified(api_key=tv_key, api_username=tv_email)
        ok("Client init", "success")
    except Exception as e:
        fail("Client init", e)
        return

    # 1. Balance
    try:
        balance = await asyncio.to_thread(lambda: client.account.balance)
        ok("Balance", f"${float(balance):.2f}")
    except Exception as e:
        fail("Balance", e)

    # 2. Services list
    try:
        services = await asyncio.to_thread(
            client.services.list,
            NumberType.MOBILE,
            ReservationType.VERIFICATION,
        )
        ok("Services", f"{len(services)} available")
        names = [s.service_name for s in services[:5]]
        info("  sample", names)
    except Exception as e:
        fail("Services", e)

    # 3. Area codes
    try:
        codes = await asyncio.to_thread(client.services.area_codes)
        ok("Area codes", f"{len(codes)} available")
        sample = [(c.area_code, c.state) for c in codes[:5]]
        info("  sample", sample)
    except Exception as e:
        fail("Area codes", e)

    # 4. Pricing for whatsapp
    try:
        price = await asyncio.to_thread(
            client.verifications.pricing,
            service_name="whatsapp",
            area_code=False,
            carrier=False,
            number_type=NumberType.MOBILE,
            capability=ReservationCapability.SMS,
        )
        ok("Whatsapp price", f"${float(price.price):.2f}")
    except Exception as e:
        fail("Whatsapp price", e)


# ── MAIN ──────────────────────────────────────────────────────────────────────

async def main():
    print("\nPROVIDER PROBE — testing all three APIs")
    print("Keys loaded from .env and script constants\n")

    await probe_telnyx()
    await probe_fivesim()
    await probe_textverified()

    print(f"\n{SEP}\nDone\n{SEP}\n")


if __name__ == "__main__":
    # Load .env manually
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())

    asyncio.run(main())
