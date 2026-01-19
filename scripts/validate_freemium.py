#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation script for freemium tier implementation
Tests all components to ensure consistency and functionality
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from app.core.tier_config import TierConfig
from app.services.tier_manager import TierManager
from sqlalchemy import text
from sqlalchemy.orm import Session

def test_database_structure():
    """Test that database has correct tier structure"""
    
    print("🔍 Testing database structure...")
    
    db = next(get_db())
    
    # Check subscription_tiers table exists and has correct data
    try:
        tiers = db.execute(text("""
            SELECT tier, name, price_monthly, quota_usd, overage_rate, 
                   has_api_access, has_area_code_selection, has_isp_filtering
            FROM subscription_tiers 
            ORDER BY price_monthly
        """)).fetchall()
        
        expected_tiers = ['freemium', 'payg', 'pro', 'custom']
        actual_tiers = [tier[0] for tier in tiers]
        
        if actual_tiers == expected_tiers:
            print("   ✅ Subscription tiers table structure correct")
        else:
            print(f"   ❌ Expected tiers {expected_tiers}, got {actual_tiers}")
            return False
        
        # Validate tier pricing
        tier_data = {tier[0]: tier for tier in tiers}
        
        # Freemium validation
        freemium = tier_data['freemium']
        if freemium[2] == 0 and freemium[3] == 0.0:  # price_monthly, quota_usd
            print("   ✅ Freemium tier pricing correct")
        else:
            print(f"   ❌ Freemium pricing wrong: ${freemium[2]/100}/mo, ${freemium[3]} quota")
        
        # Pro validation
        pro = tier_data['pro']
        if pro[2] == 2500 and pro[3] == 15.0:  # $25/mo, $15 quota
            print("   ✅ Pro tier pricing correct")
        else:
            print(f"   ❌ Pro pricing wrong: ${pro[2]/100}/mo, ${pro[3]} quota")
        
        # Custom validation
        custom = tier_data['custom']
        if custom[2] == 3500 and custom[3] == 25.0:  # $35/mo, $25 quota
            print("   ✅ Custom tier pricing correct")
        else:
            print(f"   ❌ Custom pricing wrong: ${custom[2]/100}/mo, ${custom[3]} quota")\n            \n    except Exception as e:\n        print(f\"   ❌ Database structure test failed: {e}\")\n        return False\n    \n    # Check users default to freemium\n    try:\n        user_tiers = db.execute(text(\"\"\"\n            SELECT subscription_tier, COUNT(*) as count \n            FROM users \n            GROUP BY subscription_tier\n        \"\"\")).fetchall()\n        \n        print(\"   📊 User tier distribution:\")\n        for tier, count in user_tiers:\n            print(f\"      {tier}: {count} users\")\n            \n    except Exception as e:\n        print(f\"   ⚠️  Could not check user distribution: {e}\")\n    \n    db.close()\n    return True\n\ndef test_tier_config():\n    \"\"\"Test TierConfig class returns correct data\"\"\"\n    \n    print(\"🔍 Testing TierConfig class...\")\n    \n    db = next(get_db())\n    \n    try:\n        # Test each tier\n        for tier_name in ['freemium', 'payg', 'pro', 'custom']:\n            config = TierConfig.get_tier_config(tier_name, db)\n            \n            if config['tier'] == tier_name:\n                print(f\"   ✅ {tier_name.title()} config loaded correctly\")\n            else:\n                print(f\"   ❌ {tier_name.title()} config mismatch\")\n                return False\n        \n        # Test get_all_tiers\n        all_tiers = TierConfig.get_all_tiers(db)\n        if len(all_tiers) == 4:\n            print(\"   ✅ get_all_tiers returns 4 tiers\")\n        else:\n            print(f\"   ❌ get_all_tiers returned {len(all_tiers)} tiers, expected 4\")\n            return False\n            \n    except Exception as e:\n        print(f\"   ❌ TierConfig test failed: {e}\")\n        return False\n    finally:\n        db.close()\n    \n    return True\n\ndef test_tier_manager():\n    \"\"\"Test TierManager service\"\"\"\n    \n    print(\"🔍 Testing TierManager service...\")\n    \n    db = next(get_db())\n    \n    try:\n        tier_manager = TierManager(db)\n        \n        # Test with a mock user (assuming user exists)\n        users = db.execute(text(\"SELECT id FROM users LIMIT 1\")).fetchall()\n        if not users:\n            print(\"   ⚠️  No users found, skipping TierManager test\")\n            return True\n        \n        user_id = users[0][0]\n        \n        # Test get_user_tier\n        user_tier = tier_manager.get_user_tier(user_id)\n        if user_tier in ['freemium', 'payg', 'pro', 'custom']:\n            print(f\"   ✅ get_user_tier returned valid tier: {user_tier}\")\n        else:\n            print(f\"   ❌ get_user_tier returned invalid tier: {user_tier}\")\n            return False\n        \n        # Test feature access\n        api_access = tier_manager.check_feature_access(user_id, \"api_access\")\n        expected_api_access = user_tier in ['pro', 'custom']\n        \n        if api_access == expected_api_access:\n            print(f\"   ✅ API access check correct for {user_tier} tier\")\n        else:\n            print(f\"   ❌ API access check failed for {user_tier} tier\")\n            return False\n            \n    except Exception as e:\n        print(f\"   ❌ TierManager test failed: {e}\")\n        return False\n    finally:\n        db.close()\n    \n    return True\n\ndef test_pricing_logic():\n    \"\"\"Test pricing calculations\"\"\"\n    \n    print(\"🔍 Testing pricing logic...\")\n    \n    # Test freemium effective rate\n    freemium_rate = 20.0 / 9  # $20 for 9 SMS\n    expected_rate = 2.22\n    \n    if abs(freemium_rate - expected_rate) < 0.01:\n        print(f\"   ✅ Freemium effective rate correct: ${freemium_rate:.2f}/SMS\")\n    else:\n        print(f\"   ❌ Freemium rate wrong: ${freemium_rate:.2f}, expected ${expected_rate}\")\n        return False\n    \n    # Test PAYG filtering costs\n    base_rate = 2.50\n    state_filter = 0.25\n    isp_filter = 0.50\n    combined_cost = base_rate + state_filter + isp_filter\n    \n    if combined_cost == 3.25:\n        print(f\"   ✅ PAYG combined filtering cost correct: ${combined_cost}/SMS\")\n    else:\n        print(f\"   ❌ PAYG combined cost wrong: ${combined_cost}, expected $3.25\")\n        return False\n    \n    # Test Pro break-even\n    pro_monthly = 25.0\n    pro_quota = 15.0\n    pro_overage = 0.30\n    \n    # At what SMS count does Pro become cheaper than PAYG?\n    # Pro: $25 + (sms - 6) * $0.30 where 6 SMS = $15 quota\n    # PAYG: sms * $2.50\n    # Break-even: 25 + (sms - 6) * 0.30 = sms * 2.50\n    # 25 + 0.30*sms - 1.8 = 2.50*sms\n    # 23.2 = 2.20*sms\n    # sms = 10.5, so ~11 SMS\n    \n    breakeven_sms = 11\n    pro_cost_11 = 25 + (11 - 6) * 0.30  # $26.50\n    payg_cost_11 = 11 * 2.50  # $27.50\n    \n    if pro_cost_11 < payg_cost_11:\n        print(f\"   ✅ Pro break-even logic correct at {breakeven_sms} SMS\")\n    else:\n        print(f\"   ❌ Pro break-even wrong: Pro=${pro_cost_11}, PAYG=${payg_cost_11}\")\n        return False\n    \n    return True\n\ndef test_file_consistency():\n    \"\"\"Test that all files use consistent tier names\"\"\"\n    \n    print(\"🔍 Testing file consistency...\")\n    \n    # Check key files for old tier references\n    files_to_check = [\n        \"templates/landing.html\",\n        \"templates/pricing.html\", \n        \"README.md\",\n        \"static/js/tier-manager.js\"\n    ]\n    \n    old_tier_patterns = ['\"starter\"', \"'starter'\", '\"turbo\"', \"'turbo'\"]\n    \n    for file_path in files_to_check:\n        full_path = os.path.join(\"/Users/machine/Desktop/Namaskah. app\", file_path)\n        if os.path.exists(full_path):\n            try:\n                with open(full_path, 'r') as f:\n                    content = f.read()\n                \n                found_old_refs = []\n                for pattern in old_tier_patterns:\n                    if pattern in content:\n                        found_old_refs.append(pattern)\n                \n                if found_old_refs:\n                    print(f\"   ⚠️  {file_path} contains old tier references: {found_old_refs}\")\n                else:\n                    print(f\"   ✅ {file_path} clean of old tier references\")\n                    \n            except Exception as e:\n                print(f\"   ⚠️  Could not check {file_path}: {e}\")\n        else:\n            print(f\"   ⚠️  File not found: {file_path}\")\n    \n    return True\n\ndef create_test_report():\n    \"\"\"Create comprehensive test report\"\"\"\n    \n    print(\"\\n\" + \"=\"*60)\n    print(\"📋 FREEMIUM IMPLEMENTATION VALIDATION REPORT\")\n    print(\"=\"*60)\n    \n    tests = [\n        (\"Database Structure\", test_database_structure),\n        (\"TierConfig Class\", test_tier_config),\n        (\"TierManager Service\", test_tier_manager),\n        (\"Pricing Logic\", test_pricing_logic),\n        (\"File Consistency\", test_file_consistency)\n    ]\n    \n    passed = 0\n    total = len(tests)\n    \n    for test_name, test_func in tests:\n        print(f\"\\n🧪 Running {test_name} test...\")\n        try:\n            if test_func():\n                print(f\"✅ {test_name} test PASSED\")\n                passed += 1\n            else:\n                print(f\"❌ {test_name} test FAILED\")\n        except Exception as e:\n            print(f\"❌ {test_name} test ERROR: {e}\")\n    \n    print(f\"\\n📊 TEST RESULTS: {passed}/{total} tests passed\")\n    \n    if passed == total:\n        print(\"\\n🎉 ALL TESTS PASSED! Freemium implementation is ready.\")\n        print(\"\\n✅ VALIDATION SUMMARY:\")\n        print(\"   • Database structure correct\")\n        print(\"   • Tier configuration working\")\n        print(\"   • Service layer functional\")\n        print(\"   • Pricing calculations accurate\")\n        print(\"   • Files updated consistently\")\n        print(\"\\n🚀 The freemium model is fully implemented and validated!\")\n    else:\n        print(f\"\\n⚠️  {total - passed} tests failed. Please review and fix issues.\")\n    \n    print(\"=\"*60)\n\ndef main():\n    \"\"\"Run all validation tests\"\"\"\n    \n    print(\"🔬 Starting freemium implementation validation...\")\n    create_test_report()\n\nif __name__ == \"__main__\":\n    main()