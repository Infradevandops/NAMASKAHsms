#!/usr/bin/env python3
"""Test TextVerified API endpoints."""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_endpoints():
    """Test different endpoints."""
    api_key = os.getenv("TEXTVERIFIED_API_KEY")
    
    endpoints = [
        "/api/pub/v2/services",
        "/api/pub/v2/area-codes", 
        "/api/pub/v2/account/me",
        "/api/pub/v2/pricing/verifications"
    ]
    
    for endpoint in endpoints:
        print(f"\n=== Testing {endpoint} ===")
        try:
            async with httpx.AsyncClient() as client:
                # Try with query parameter
                response = await client.get(
                    f"https://www.textverified.com{endpoint}",
                    params={"apikey": api_key},
                    timeout=10.0
                )
                print(f"Query param - Status: {response.status_code}")
                if response.status_code != 401:
                    print(f"Response: {response.text[:200]}")
                
                # Try with different header format
                response = await client.get(
                    f"https://www.textverified.com{endpoint}",
                    headers={"apikey": api_key},
                    timeout=10.0
                )
                print(f"Header - Status: {response.status_code}")
                if response.status_code != 401:
                    print(f"Response: {response.text[:200]}")
                    
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())