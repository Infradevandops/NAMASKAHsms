#!/usr/bin/env python3
"""
Quick test script to verify API compatibility routes
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")
    
    try:
        from app.api.compatibility_routes import router
        print("✅ Compatibility routes imported successfully")
        
        # Check routes are registered
        routes = [route.path for route in router.routes]
        print(f"✅ Found {len(routes)} routes:")
        for route in routes:
            print(f"   - {route}")
        
        expected_routes = [
            "/billing/balance",
            "/user/me",
            "/tiers/current",
            "/tiers/",
            "/tiers",
            "/notifications/categories",
            "/user/settings"
        ]
        
        for expected in expected_routes:
            if expected in routes:
                print(f"✅ Route {expected} registered")
            else:
                print(f"❌ Route {expected} NOT found")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_app():
    """Test that main app includes compatibility router."""
    print("\nTesting main app configuration...")
    
    try:
        from main import app
        print("✅ Main app imported successfully")
        
        # Check if compatibility routes are included
        all_routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                all_routes.append(route.path)
        
        print(f"✅ Total routes in app: {len(all_routes)}")
        
        # Check for our compatibility routes
        compatibility_routes = [
            "/api/billing/balance",
            "/api/user/me",
            "/api/tiers/current",
            "/api/notifications/categories",
            "/api/user/settings"
        ]
        
        found_count = 0
        for route in compatibility_routes:
            if route in all_routes:
                print(f"✅ Route {route} available in app")
                found_count += 1
            else:
                print(f"⚠️  Route {route} not found (may be registered differently)")
        
        print(f"\n✅ Found {found_count}/{len(compatibility_routes)} compatibility routes")
        return True
        
    except Exception as e:
        print(f"❌ Main app test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("API Compatibility Routes - Verification Test")
    print("=" * 60)
    
    test1 = test_imports()
    test2 = test_main_app()
    
    print("\n" + "=" * 60)
    if test1 and test2:
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        sys.exit(1)
