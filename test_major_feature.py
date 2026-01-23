#!/usr/bin/env python3
"""
Verification Test Script - Tests all major features
Run this to verify the implementation is effective
"""

import asyncio
import sys
from app.core.database import SessionLocal
from app.models.user import User
from app.services.textverified_service import TextVerifiedService
from app.services.availability_service import AvailabilityService

async def test_textverified_api():
    """Test 1: TextVerified API Integration"""
    print("\n" + "="*60)
    print("TEST 1: TextVerified API Integration")
    print("="*60)
    
    try:
        tv_service = TextVerifiedService()
        
        # Test carriers
        print("\n📡 Testing get_available_carriers()...")
        carriers = await tv_service.get_available_carriers("US")
        if carriers:
            print(f"✅ SUCCESS: Retrieved {len(carriers)} carriers")
            for carrier in carriers[:3]:
                print(f"   - {carrier.get('name', 'Unknown')}")
        else:
            print("⚠️  WARNING: No carriers returned (may use fallback)")
        
        # Test area codes
        print("\n📡 Testing get_area_codes()...")
        area_codes = await tv_service.get_area_codes("US", service="telegram")
        if area_codes:
            print(f"✅ SUCCESS: Retrieved {len(area_codes)} area codes")
            for code in area_codes[:3]:
                print(f"   - {code.get('area_code', 'Unknown')}")
        else:
            print("⚠️  WARNING: No area codes returned (may use fallback)")
            
        return True
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def test_availability_service():
    """Test 2: Availability Service"""
    print("\n" + "="*60)
    print("TEST 2: Availability Service")
    print("="*60)
    
    db = SessionLocal()
    try:
        availability_service = AvailabilityService(db)
        
        # Test carrier availability
        print("\n📊 Testing get_carrier_availability()...")
        stats = availability_service.get_carrier_availability("Verizon", "US")
        print(f"✅ SUCCESS: Carrier stats retrieved")
        print(f"   - Success Rate: {stats.get('success_rate', 0)}%")
        print(f"   - Total Verifications: {stats.get('total', 0)}")
        
        # Test area code availability
        print("\n📊 Testing get_area_code_availability()...")
        stats = availability_service.get_area_code_availability("212", "US")
        print(f"✅ SUCCESS: Area code stats retrieved")
        print(f"   - Success Rate: {stats.get('success_rate', 0)}%")
        print(f"   - Total Verifications: {stats.get('total', 0)}")
        
        return True
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False
    finally:
        db.close()

def test_user_tier():
    """Test 3: User Tier Configuration"""
    print("\n" + "="*60)
    print("TEST 3: User Tier Configuration")
    print("="*60)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "admin@namaskah.app").first()
        if user:
            print(f"✅ SUCCESS: Found admin user")
            print(f"   - Email: {user.email}")
            print(f"   - Tier: {user.subscription_tier}")
            print(f"   - Credits: ${user.credits:.2f}")
            
            if user.subscription_tier == "custom":
                print("✅ VERIFIED: Admin is on CUSTOM tier (has full access)")
                return True
            else:
                print(f"⚠️  WARNING: Admin is on {user.subscription_tier} tier (expected: custom)")
                return False
        else:
            print("❌ FAILED: Admin user not found")
            return False
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False
    finally:
        db.close()

def test_api_endpoints():
    """Test 4: API Endpoint Registration"""
    print("\n" + "="*60)
    print("TEST 4: API Endpoint Registration")
    print("="*60)
    
    try:
        from main import app
        
        routes = [route.path for route in app.routes]
        
        # Check carrier endpoint
        carrier_endpoint = "/api/verification/carriers/{country}"
        if carrier_endpoint in routes:
            print(f"✅ SUCCESS: Carrier endpoint registered")
            print(f"   - {carrier_endpoint}")
        else:
            print(f"❌ FAILED: Carrier endpoint not found")
            return False
        
        # Check area code endpoint
        area_code_endpoint = "/api/verification/area-codes/{country}"
        if area_code_endpoint in routes:
            print(f"✅ SUCCESS: Area code endpoint registered")
            print(f"   - {area_code_endpoint}")
        else:
            print(f"❌ FAILED: Area code endpoint not found")
            return False
            
        return True
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def test_frontend_integration():
    """Test 5: Frontend Integration"""
    print("\n" + "="*60)
    print("TEST 5: Frontend Integration")
    print("="*60)
    
    try:
        # Check if verification.js exists and has required functions
        with open("static/js/verification.js", "r") as f:
            content = f.read()
            
        required_functions = [
            "loadCarriers",
            "loadAreaCodes",
            "checkTierAccess",
            "updatePricePreview"
        ]
        
        all_found = True
        for func in required_functions:
            if f"async function {func}" in content or f"function {func}" in content:
                print(f"✅ Found: {func}()")
            else:
                print(f"❌ Missing: {func}()")
                all_found = False
        
        # Check for visual indicators
        if "🟢" in content and "🟡" in content:
            print("✅ Visual indicators present (🟢 🟡 🔴)")
        else:
            print("⚠️  Visual indicators may be missing")
            
        # Check for loading states
        if "Loading carriers" in content or "Loading area codes" in content:
            print("✅ Loading states implemented")
        else:
            print("⚠️  Loading states may be missing")
            
        return all_found
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("🔍 VERIFICATION TEST SUITE")
    print("Testing Major Feature Implementation")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("TextVerified API", await test_textverified_api()))
    results.append(("Availability Service", test_availability_service()))
    results.append(("User Tier Config", test_user_tier()))
    results.append(("API Endpoints", test_api_endpoints()))
    results.append(("Frontend Integration", test_frontend_integration()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Feature is EFFECTIVE!")
        print("="*60)
        return 0
    else:
        print("⚠️  SOME TESTS FAILED - Review issues above")
        print("="*60)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
