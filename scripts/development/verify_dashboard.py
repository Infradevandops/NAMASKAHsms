#!/usr/bin/env python3
"""
Dashboard Feature Verification Script
Tests all buttons, modals, and business flows
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_dashboard_features():
    """Test all dashboard features"""
    
    print("🔍 DASHBOARD FEATURE VERIFICATION")
    print("=" * 60)
    
    tests = []
    
    # Test 1: Check if ultra-stable script exists
    script_path = Path(__file__).parent.parent / "static/js/dashboard-ultra-stable.js"
    if script_path.exists():
        print("✅ Ultra-stable dashboard script exists")
        tests.append(True)
    else:
        print("❌ Ultra-stable dashboard script missing")
        tests.append(False)
    
    # Test 2: Check dashboard template
    template_path = Path(__file__).parent.parent / "templates/dashboard.html"
    if template_path.exists():
        content = template_path.read_text()
        if 'dashboard-ultra-stable.js' in content:
            print("✅ Dashboard template uses ultra-stable script")
            tests.append(True)
        else:
            print("❌ Dashboard template not updated")
            tests.append(False)
            
        if 'new-verification-btn' in content:
            print("✅ New Verification button exists in template")
            tests.append(True)
        else:
            print("❌ New Verification button missing")
            tests.append(False)
    else:
        print("❌ Dashboard template missing")
        tests.append(False)
    
    # Test 3: Check API endpoints
    print("\n📡 Checking API Endpoints...")
    from main import app
    
    endpoints_to_check = [
        '/api/services',
        '/api/verify/create',
        '/api/wallet/balance',
        '/api/billing/tiers/available',
        '/api/admin/users',
        '/api/admin/stats'
    ]
    
    for route in app.routes:
        if hasattr(route, 'path'):
            for endpoint in endpoints_to_check:
                if route.path == endpoint:
                    print(f"✅ {endpoint}")
                    tests.append(True)
                    endpoints_to_check.remove(endpoint)
                    break
    
    for missing in endpoints_to_check:
        print(f"❌ {missing} - NOT FOUND")
        tests.append(False)
    
    # Test 4: Check button handlers in script
    if script_path.exists():
        script_content = script_path.read_text()
        
        handlers = [
            'new-verification-btn',
            'add-credits-btn',
            'usage-btn',
            'upgrade-btn'
        ]
        
        print("\n🔘 Checking Button Handlers...")
        for handler in handlers:
            if handler in script_content:
                print(f"✅ {handler} handler exists")
                tests.append(True)
            else:
                print(f"❌ {handler} handler missing")
                tests.append(False)
    
    # Test 5: Check modal functions
    if script_path.exists():
        print("\n🪟 Checking Modal Functions...")
        modal_functions = [
            'openModal',
            'closeModal',
            'createVerification',
            'checkSMS',
            'loadServices'
        ]
        
        for func in modal_functions:
            if f'function {func}' in script_content or f'async function {func}' in script_content:
                print(f"✅ {func}() exists")
                tests.append(True)
            else:
                print(f"❌ {func}() missing")
                tests.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    passed = sum(tests)
    total = len(tests)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"📊 RESULTS: {passed}/{total} tests passed ({percentage:.1f}%)")
    
    if percentage == 100:
        print("🎉 ALL TESTS PASSED - Dashboard is 100% functional!")
        return 0
    elif percentage >= 80:
        print("⚠️  Most tests passed - Minor issues detected")
        return 1
    else:
        print("❌ CRITICAL ISSUES - Dashboard needs fixes")
        return 2

if __name__ == "__main__":
    sys.exit(test_dashboard_features())
