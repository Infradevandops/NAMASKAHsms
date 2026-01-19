#!/usr/bin/env python3
"""
Verify Dashboard Fixes Implementation
Tests translation system and tier display functionality
"""

import json
import os


def verify_translation_files():
    """Verify translation files exist and have correct structure"""

    print("🔍 Verifying Translation Files...\n")

    base_path = "/Users/machine/Desktop/Namaskah. app/static/locales"

    # Check English translations
    en_path = f"{base_path}/en.json"
    if os.path.exists(en_path):
        with open(en_path, "r") as f:
            en_data = json.load(f)

        required_keys = ["dashboard", "tiers"]
        missing = [k for k in required_keys if k not in en_data]

        if not missing:
            print("✅ English translations (en.json):")
            print(f"   - dashboard keys: {len(en_data.get('dashboard', {}))}")
            print(f"   - tier keys: {len(en_data.get('tiers', {}))}")
            print(
                f"   - tier feature keys: {len(en_data.get('tiers', {}).get('features', {}))}"
            )
        else:
            print(f"❌ English translations missing keys: {missing}")
            return False
    else:
        print(f"❌ English translation file not found: {en_path}")
        return False

    # Check Spanish translations
    es_path = f"{base_path}/es.json"
    if os.path.exists(es_path):
        with open(es_path, "r") as f:
            es_data = json.load(f)

        if "dashboard" in es_data and "tiers" in es_data:
            print("\n✅ Spanish translations (es.json):")
            print(f"   - dashboard keys: {len(es_data.get('dashboard', {}))}")
            print(f"   - tier keys: {len(es_data.get('tiers', {}))}")
            print(
                f"   - tier feature keys: {len(es_data.get('tiers', {}).get('features', {}))}"
            )

            # Verify key translations
            print("\n📋 Sample Spanish Translations:")
            print(f"   Dashboard → {es_data['dashboard']['title']}")
            print(f"   Total SMS → {es_data['dashboard']['total_sms']}")
            print(f"   Successful → {es_data['dashboard']['successful']}")
            print(f"   Freemium → {es_data['tiers']['freemium']}")
            print(f"   Pay-As-You-Go → {es_data['tiers']['payg']}")
        else:
            print(f"❌ Spanish translations missing required keys")
            return False
    else:
        print(f"❌ Spanish translation file not found: {es_path}")
        return False

    return True


def verify_dashboard_template():
    """Verify dashboard template has i18n attributes"""

    print("\n🔍 Verifying Dashboard Template...\n")

    template_path = "/Users/machine/Desktop/Namaskah. app/templates/dashboard.html"

    if not os.path.exists(template_path):
        print(f"❌ Dashboard template not found: {template_path}")
        return False

    with open(template_path, "r") as f:
        content = f.read()

    # Check for i18n attributes
    i18n_checks = [
        ('data-i18n="dashboard.title"', "Dashboard title"),
        ('data-i18n="dashboard.subtitle"', "Dashboard subtitle"),
        ('data-i18n="dashboard.total_sms"', "Total SMS label"),
        ('data-i18n="dashboard.successful"', "Successful label"),
        ('data-i18n="dashboard.total_spent"', "Total Spent label"),
        ('data-i18n="dashboard.success_rate"', "Success Rate label"),
        ('data-i18n="dashboard.recent_activity"', "Recent Activity label"),
        ('data-i18n="tiers.current_plan"', "Current Plan label"),
    ]

    all_found = True
    for check, description in i18n_checks:
        if check in content:
            print(f"✅ {description}: i18n attribute present")
        else:
            print(f"❌ {description}: i18n attribute MISSING")
            all_found = False

    # Check for tier card
    if 'id="tier-card"' in content:
        print("\n✅ Tier information card: Present")
    else:
        print("\n❌ Tier information card: MISSING")
        all_found = False

    # Check for tier loading function
    if "async function loadTierInfo()" in content:
        print("✅ Tier loading function: Present")
    else:
        print("❌ Tier loading function: MISSING")
        all_found = False

    # Check for i18n initialization
    if "await i18n.loadTranslations()" in content:
        print("✅ i18n initialization: Present")
    else:
        print("❌ i18n initialization: MISSING")
        all_found = False

    # Check for tier features logic
    tier_checks = ["freemium", "payg", "pro", "custom"]
    tier_logic_found = all(tier in content for tier in tier_checks)

    if tier_logic_found:
        print("✅ Tier-specific feature logic: Present for all tiers")
    else:
        print("❌ Tier-specific feature logic: INCOMPLETE")
        all_found = False

    return all_found


def verify_i18n_system():
    """Verify i18n.js exists and is properly configured"""

    print("\n🔍 Verifying i18n System...\n")

    i18n_path = "/Users/machine/Desktop/Namaskah. app/static/js/i18n.js"

    if not os.path.exists(i18n_path):
        print(f"❌ i18n.js not found: {i18n_path}")
        return False

    with open(i18n_path, "r") as f:
        content = f.read()

    required_functions = [
        ("loadTranslations", "Load translations function"),
        ("translatePage", "Translate page function"),
        ("changeLanguage", "Change language function"),
        ("data-i18n", "i18n attribute selector"),
    ]

    all_found = True
    for func, description in required_functions:
        if func in content:
            print(f"✅ {description}: Present")
        else:
            print(f"❌ {description}: MISSING")
            all_found = False

    return all_found


def create_test_report():
    """Generate comprehensive test report"""

    print("\n" + "=" * 60)
    print("📋 DASHBOARD FIXES VERIFICATION REPORT")
    print("=" * 60)

    tests = [
        ("Translation Files", verify_translation_files),
        ("Dashboard Template", verify_dashboard_template),
        ("i18n System", verify_i18n_system),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ {test_name} test ERROR: {e}")

    print("\n" + "=" * 60)
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n✅ ALL VERIFICATIONS PASSED!")
        print("\n🎉 Implementation is correct:")
        print("   ✅ Translation files properly structured")
        print("   ✅ Dashboard template has i18n attributes")
        print("   ✅ Tier information card implemented")
        print("   ✅ i18n system configured correctly")
        print("\n🚀 Ready to test in browser!")
        print("\n📝 Next Steps:")
        print("   1. Refresh browser (Cmd+Shift+R)")
        print("   2. Login to dashboard")
        print("   3. Change language to Español")
        print("   4. Verify translations work")
        print("   5. Verify tier card displays")
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        print("   Please review the errors above")

    print("=" * 60)


if __name__ == "__main__":
    print("🔬 Starting Dashboard Fixes Verification...\n")
    create_test_report()
