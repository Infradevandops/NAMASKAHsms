#!/usr/bin/env python3
"""
Telnyx API Capability Test
Tests area code filtering, carrier lookup, and international support
"""

import os
import sys
import asyncio
import httpx
from typing import Dict, Any

# Load from .env
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY", "")
BASE_URL = "https://api.telnyx.com/v2"


class TelnyxTester:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(timeout=30.0)

    async def test_us_area_code_search(self, area_code: str = "415") -> Dict[str, Any]:
        """Test 1: Can we search US numbers by area code?"""
        print(f"\n{'='*60}")
        print(f"TEST 1: US Area Code Search (Area Code: {area_code})")
        print(f"{'='*60}")

        try:
            response = await self.client.get(
                f"{BASE_URL}/available_phone_numbers",
                headers=self.headers,
                params={
                    "filter[country_code]": "US",
                    "filter[national_destination_code]": area_code,
                    "filter[features]": "sms",
                    "filter[limit]": 5,
                },
            )

            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                numbers = data.get("data", [])

                print(f"✅ SUCCESS: Found {len(numbers)} numbers")

                if numbers:
                    print(f"\nSample Numbers:")
                    for num in numbers[:3]:
                        phone = num.get("phone_number")
                        region = num.get("region_information", [{}])[0]
                        print(f"  - {phone}")
                        print(f"    Region: {region.get('region_name', 'N/A')}")
                        print(f"    Rate Center: {region.get('rate_center', 'N/A')}")

                return {
                    "supported": True,
                    "area_code": area_code,
                    "count": len(numbers),
                    "sample": numbers[0].get("phone_number") if numbers else None,
                }
            else:
                print(f"❌ FAILED: {response.text}")
                return {"supported": False, "error": response.text}

        except Exception as e:
            print(f"❌ ERROR: {e}")
            return {"supported": False, "error": str(e)}

    async def test_international_area_code(
        self, country: str = "GB", prefix: str = "20"
    ) -> Dict[str, Any]:
        """Test 2: Can we search international numbers by area code/prefix?"""
        print(f"\n{'='*60}")
        print(
            f"TEST 2: International Area Code Search (Country: {country}, Prefix: {prefix})"
        )
        print(f"{'='*60}")

        try:
            response = await self.client.get(
                f"{BASE_URL}/available_phone_numbers",
                headers=self.headers,
                params={
                    "filter[country_code]": country,
                    "filter[national_destination_code]": prefix,
                    "filter[features]": "sms",
                    "filter[limit]": 5,
                },
            )

            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                numbers = data.get("data", [])

                print(f"✅ SUCCESS: Found {len(numbers)} numbers")

                if numbers:
                    print(f"\nSample Numbers:")
                    for num in numbers[:3]:
                        phone = num.get("phone_number")
                        region = num.get("region_information", [{}])[0]
                        print(f"  - {phone}")
                        print(f"    Region: {region.get('region_name', 'N/A')}")

                return {
                    "supported": True,
                    "country": country,
                    "prefix": prefix,
                    "count": len(numbers),
                    "sample": numbers[0].get("phone_number") if numbers else None,
                }
            else:
                print(f"❌ FAILED: {response.text}")
                return {"supported": False, "error": response.text}

        except Exception as e:
            print(f"❌ ERROR: {e}")
            return {"supported": False, "error": str(e)}

    async def test_carrier_lookup(
        self, phone_number: str = "+14155551234"
    ) -> Dict[str, Any]:
        """Test 3: Can we lookup carrier information?"""
        print(f"\n{'='*60}")
        print(f"TEST 3: Carrier Lookup (Number: {phone_number})")
        print(f"{'='*60}")

        try:
            response = await self.client.get(
                f"{BASE_URL}/number_lookup/{phone_number}",
                headers=self.headers,
                params={"type": "carrier"},
            )

            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                carrier_data = data.get("data", {}).get("carrier", {})

                print(f"✅ SUCCESS: Carrier lookup available")
                print(f"\nCarrier Information:")
                print(f"  Name: {carrier_data.get('name', 'N/A')}")
                print(f"  Type: {carrier_data.get('type', 'N/A')}")
                print(
                    f"  Mobile Network Code: {carrier_data.get('mobile_network_code', 'N/A')}"
                )
                print(
                    f"  Mobile Country Code: {carrier_data.get('mobile_country_code', 'N/A')}"
                )

                return {
                    "supported": True,
                    "carrier": carrier_data.get("name"),
                    "type": carrier_data.get("type"),
                    "is_mobile": carrier_data.get("type") == "mobile",
                }
            else:
                print(f"❌ FAILED: {response.text}")
                return {"supported": False, "error": response.text}

        except Exception as e:
            print(f"❌ ERROR: {e}")
            return {"supported": False, "error": str(e)}

    async def test_number_purchase(self, phone_number: str) -> Dict[str, Any]:
        """Test 4: Can we purchase a number? (DRY RUN - won't actually purchase)"""
        print(f"\n{'='*60}")
        print(f"TEST 4: Number Purchase API (DRY RUN)")
        print(f"{'='*60}")

        print(f"📝 Would purchase: {phone_number}")
        print(f"✅ Purchase endpoint exists: POST /phone_numbers")

        return {
            "supported": True,
            "endpoint": f"{BASE_URL}/phone_numbers",
            "method": "POST",
            "note": "Not tested to avoid charges",
        }

    async def test_messaging_profile(self) -> Dict[str, Any]:
        """Test 5: Check messaging profiles for SMS"""
        print(f"\n{'='*60}")
        print(f"TEST 5: Messaging Profiles")
        print(f"{'='*60}")

        try:
            response = await self.client.get(
                f"{BASE_URL}/messaging_profiles", headers=self.headers
            )

            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                profiles = data.get("data", [])

                print(f"✅ SUCCESS: Found {len(profiles)} messaging profiles")

                if profiles:
                    print(f"\nSample Profile:")
                    profile = profiles[0]
                    print(f"  ID: {profile.get('id')}")
                    print(f"  Name: {profile.get('name')}")
                    print(f"  Enabled: {profile.get('enabled')}")

                return {"supported": True, "count": len(profiles)}
            else:
                print(f"❌ FAILED: {response.text}")
                return {"supported": False, "error": response.text}

        except Exception as e:
            print(f"❌ ERROR: {e}")
            return {"supported": False, "error": str(e)}

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run complete test suite"""
        print(f"\n{'#'*60}")
        print(f"# TELNYX API CAPABILITY TEST")
        print(f"{'#'*60}")

        results = {"provider": "Telnyx", "tests": {}}

        # Test 1: US Area Code
        results["tests"]["us_area_code"] = await self.test_us_area_code_search("415")
        await asyncio.sleep(1)

        # Test 2: International Area Code (London)
        results["tests"]["intl_area_code_london"] = (
            await self.test_international_area_code("GB", "20")
        )
        await asyncio.sleep(1)

        # Test 3: International Area Code (Berlin)
        results["tests"]["intl_area_code_berlin"] = (
            await self.test_international_area_code("DE", "30")
        )
        await asyncio.sleep(1)

        # Test 4: Carrier Lookup
        results["tests"]["carrier_lookup"] = await self.test_carrier_lookup(
            "+14155551234"
        )
        await asyncio.sleep(1)

        # Test 5: Messaging Profiles
        results["tests"]["messaging_profiles"] = await self.test_messaging_profile()

        # Calculate score
        score = 0
        if results["tests"]["us_area_code"].get("supported"):
            score += 3
        if results["tests"]["intl_area_code_london"].get("supported"):
            score += 3
        if results["tests"]["carrier_lookup"].get("supported"):
            score += 2
        if results["tests"]["messaging_profiles"].get("supported"):
            score += 2

        results["score"] = f"{score}/10"

        # Print summary
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"Provider: Telnyx")
        print(f"Score: {results['score']}")
        print(f"\nFeature Support:")
        print(
            f"  US Area Code Filtering: {'✅' if results['tests']['us_area_code'].get('supported') else '❌'}"
        )
        print(
            f"  International Area Code (London): {'✅' if results['tests']['intl_area_code_london'].get('supported') else '❌'}"
        )
        print(
            f"  International Area Code (Berlin): {'✅' if results['tests']['intl_area_code_berlin'].get('supported') else '❌'}"
        )
        print(
            f"  Carrier Lookup: {'✅' if results['tests']['carrier_lookup'].get('supported') else '❌'}"
        )
        print(
            f"  Messaging Profiles: {'✅' if results['tests']['messaging_profiles'].get('supported') else '❌'}"
        )

        if score >= 8:
            print(
                f"\n🎉 RECOMMENDATION: ✅ EXCELLENT - Proceed with Telnyx integration"
            )
        elif score >= 6:
            print(f"\n🟡 RECOMMENDATION: GOOD - Consider Telnyx with some limitations")
        else:
            print(f"\n❌ RECOMMENDATION: POOR - Look for alternatives")

        print(f"{'='*60}\n")

        return results

    async def close(self):
        await self.client.aclose()


async def main():
    tester = TelnyxTester(TELNYX_API_KEY)

    try:
        results = await tester.run_all_tests()

        # Save results to file
        import json

        with open("telnyx_test_results.json", "w") as f:
            json.dump(results, f, indent=2)

        print(f"📄 Results saved to: telnyx_test_results.json")

    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
