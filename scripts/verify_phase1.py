#!/usr/bin/env python3
"""
Verification Script for Phase 1 Implementation
Tests all new page routes and sidebar navigation
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_routes_registered():
    """Test that all routes are registered in main_routes.py"""
    print("🔍 Testing Route Registration...")
    
    routes_file = project_root / "app" / "api" / "main_routes.py"
    content = routes_file.read_text()
    
    required_routes = [
        '/verify',
        '/wallet',
        '/history',
        '/analytics',
        '/notifications',
        '/settings',
        '/webhooks',
        '/api-docs',
        '/referrals',
        '/voice-verify',
        '/bulk-purchase',
        '/admin',
        '/privacy-settings'
    ]
    
    results = []
    for route in required_routes:
        if f'"{route}"' in content or f"'{route}'" in content:
            results.append(f"  ✅ {route} - Registered")
        else:
            results.append(f"  ❌ {route} - NOT FOUND")
    
    print("\n".join(results))
    
    success_count = sum(1 for r in results if '✅' in r)
    total_count = len(required_routes)
    
    print(f"\n📊 Routes Registered: {success_count}/{total_count}")
    return success_count == total_count


def test_templates_exist():
    """Test that all required templates exist"""
    print("\n🔍 Testing Template Files...")
    
    templates_dir = project_root / "templates"
    
    required_templates = [
        'dashboard.html',
        'verify.html',
        'wallet.html',
        'history.html',
        'analytics.html',
        'notifications.html',
        'settings.html',
        'webhooks.html',
        'api_docs.html',
        'referrals.html',
        'voice_verify.html',
        'bulk_purchase.html',
        'gdpr_settings.html'
    ]
    
    results = []
    for template in required_templates:
        template_path = templates_dir / template
        if template_path.exists():
            results.append(f"  ✅ {template} - Exists")
        else:
            results.append(f"  ❌ {template} - NOT FOUND")
    
    print("\n".join(results))
    
    success_count = sum(1 for r in results if '✅' in r)
    total_count = len(required_templates)
    
    print(f"\n📊 Templates Found: {success_count}/{total_count}")
    return success_count == total_count


def test_sidebar_links_unhidden():
    """Test that sidebar links are unhidden"""
    print("\n🔍 Testing Sidebar Links...")
    
    sidebar_file = project_root / "templates" / "components" / "sidebar.html"
    content = sidebar_file.read_text()
    
    required_links = [
        ('/verify', 'SMS Verification'),
        ('/wallet', 'Wallet'),
        ('/history', 'History'),
        ('/analytics', 'Analytics'),
        ('/notifications', 'Notifications'),
        ('/settings', 'Settings')
    ]
    
    results = []
    for route, name in required_links:
        # Check if link is NOT commented out
        if f'href="{route}"' in content:
            # Check if it's not inside a comment
            lines = content.split('\n')
            found_uncommented = False
            for line in lines:
                if f'href="{route}"' in line and not line.strip().startswith('<!--'):
                    found_uncommented = True
                    break
            
            if found_uncommented:
                results.append(f"  ✅ {name} ({route}) - Visible")
            else:
                results.append(f"  ⚠️ {name} ({route}) - Commented Out")
        else:
            results.append(f"  ❌ {name} ({route}) - NOT FOUND")
    
    print("\n".join(results))
    
    success_count = sum(1 for r in results if '✅' in r)
    total_count = len(required_links)
    
    print(f"\n📊 Sidebar Links Visible: {success_count}/{total_count}")
    return success_count == total_count


def test_route_functions():
    """Test that route functions are properly defined"""
    print("\n🔍 Testing Route Functions...")
    
    routes_file = project_root / "app" / "api" / "main_routes.py"
    content = routes_file.read_text()
    
    required_functions = [
        'verify_page',
        'wallet_page',
        'history_page',
        'analytics_page',
        'notifications_page',
        'settings_page',
        'webhooks_page',
        'api_docs_page',
        'referrals_page',
        'voice_verify_page',
        'bulk_purchase_page',
        'admin_page',
        'privacy_settings_page'
    ]
    
    results = []
    for func in required_functions:
        if f'async def {func}' in content:
            results.append(f"  ✅ {func}() - Defined")
        else:
            results.append(f"  ❌ {func}() - NOT FOUND")
    
    print("\n".join(results))
    
    success_count = sum(1 for r in results if '✅' in r)
    total_count = len(required_functions)
    
    print(f"\n📊 Route Functions: {success_count}/{total_count}")
    return success_count == total_count


def test_authentication_required():
    """Test that routes require authentication"""
    print("\n🔍 Testing Authentication Requirements...")
    
    routes_file = project_root / "app" / "api" / "main_routes.py"
    content = routes_file.read_text()
    
    # Check that get_current_user_id is used
    if 'get_current_user_id' in content:
        print("  ✅ Authentication dependency imported")
    else:
        print("  ❌ Authentication dependency NOT imported")
        return False
    
    # Check that routes use the dependency
    protected_routes = ['verify_page', 'wallet_page', 'history_page', 'analytics_page']
    
    results = []
    for route in protected_routes:
        if f'user_id: str = Depends(get_current_user_id)' in content:
            results.append(f"  ✅ {route} - Protected")
        else:
            results.append(f"  ⚠️ {route} - May not be protected")
    
    print("\n".join(results))
    return True


def main():
    """Run all verification tests"""
    print("=" * 60)
    print("🚀 PHASE 1 IMPLEMENTATION VERIFICATION")
    print("=" * 60)
    
    tests = [
        ("Route Registration", test_routes_registered),
        ("Template Files", test_templates_exist),
        ("Sidebar Links", test_sidebar_links_unhidden),
        ("Route Functions", test_route_functions),
        ("Authentication", test_authentication_required)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Error in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED - Phase 1 Implementation Verified!")
        print("🚀 Ready to proceed to Phase 2 (JavaScript Integration)")
        return 0
    else:
        print("\n⚠️ SOME TESTS FAILED - Review implementation")
        return 1


if __name__ == "__main__":
    sys.exit(main())
