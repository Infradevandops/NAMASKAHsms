#!/usr/bin/env python3
"""Quick test of TextVerified API authentication."""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_textverified_auth():
    """Test different authentication methods."""
    api_key = os.getenv("TEXTVERIFIED_API_KEY")
    email = os.getenv("TEXTVERIFIED_EMAIL")
    
    print(f"API Key: {api_key[:10]}..." if api_key else "No API key")
    print(f"Email: {email}")
    
    # Test 1: Direct API key in header
    print("\n=== Test 1: API Key in Authorization header ===")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.textverified.com/api/pub/v2/account/me",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                timeout=10.0
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: API key as query parameter
    print("\n=== Test 2: API Key as query parameter ===")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.textverified.com/api/pub/v2/account/me",
                params={"api_key": api_key},
                timeout=10.0
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: API key in custom header
    print("\n=== Test 3: API Key in X-API-Key header ===")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.textverified.com/api/pub/v2/account/me",
                headers={
                    "X-API-Key": api_key,
                    "Content-Type": "application/json"
                },
                timeout=10.0
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_textverified_auth())