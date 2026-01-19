#!/usr/bin/env python3
"""
Comprehensive analysis to check for potential breaking changes from removed files
"""

import os
import re
import glob
from collections import defaultdict


def analyze_removed_files_impact():
    """Analyze impact of removed files on the codebase."""

    print("🔍 COMPREHENSIVE BREAKING CHANGE ANALYSIS")
    print("=" * 60)

    # Files that were removed
    removed_files = [
        "app/services/textverified_integration.py",
        "app/services/textverified_api.py",
        "app/services/textverified_provider.py",
        "app/services/textverified_polling_service.py",
        "app/services/textverified_auth.py",
        "app/services/pricing_service.py",
        "app/services/oauth_service.py",
    ]

    # Check for any remaining references
    print("\n📊 CHECKING FOR REMAINING REFERENCES:")

    for removed_file in removed_files:
        module_name = (
            removed_file.replace("app/", "").replace(".py", "").replace("/", ".")
        )
        print(f"\n🔍 Analyzing: {removed_file}")

        # Search for imports
        import_patterns = [
            f"from {module_name} import",
            f"import {module_name}",
            module_name.split(".")[-1],  # Just the class name
        ]

        references_found = []

        for root, dirs, files in os.walk("app"):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r") as f:
                            content = f.read()
                            for pattern in import_patterns:
                                if pattern in content:
                                    references_found.append((filepath, pattern))
                    except:
                        pass

        if references_found:
            print(f"  ❌ POTENTIAL ISSUES FOUND:")
            for filepath, pattern in references_found:
                print(f"    - {filepath}: '{pattern}'")
        else:
            print(f"  ✅ No references found - Safe removal")


def check_main_py_imports():
    """Check main.py for any broken imports."""
    print("\n🔍 CHECKING MAIN.PY IMPORTS:")

    if os.path.exists("main.py"):
        with open("main.py", "r") as f:
            content = f.read()

        # Check for removed service imports
        removed_imports = [
            "textverified_integration",
            "textverified_api",
            "textverified_provider",
            "textverified_polling_service",
            "textverified_auth",
            "pricing_service",
            "oauth_service",
        ]

        issues = []
        for removed in removed_imports:
            if removed in content:
                issues.append(removed)

        if issues:
            print(f"  ❌ BROKEN IMPORTS FOUND:")
            for issue in issues:
                print(f"    - {issue}")
        else:
            print(f"  ✅ No broken imports in main.py")


def test_core_functionality():
    """Test that core functionality still works."""
    print("\n🔍 TESTING CORE FUNCTIONALITY:")

    try:
        # Test pricing system
        from app.services.pricing_calculator import PricingCalculator
        from app.core.database import SessionLocal

        db = SessionLocal()
        calculator = PricingCalculator(db)
        tiers = calculator.get_all_tiers()
        db.close()

        print(f"  ✅ Pricing system: {len(tiers)} tiers loaded")

    except Exception as e:
        print(f"  ❌ Pricing system error: {e}")

    try:
        # Test TextVerified service
        from app.services.textverified_service import TextVerifiedService

        tv_service = TextVerifiedService()
        print(f"  ✅ TextVerified service: initialized")

    except Exception as e:
        print(f"  ❌ TextVerified service error: {e}")

    try:
        # Test API endpoints
        from app.api.billing.tier_endpoints import router as tier_router
        from app.api.billing.pricing_endpoints import router as pricing_router

        print(f"  ✅ API routers: tier and pricing loaded")

    except Exception as e:
        print(f"  ❌ API router error: {e}")


def check_database_dependencies():
    """Check if removed services had database dependencies."""
    print("\n🔍 CHECKING DATABASE DEPENDENCIES:")

    try:
        from app.core.database import SessionLocal
        from sqlalchemy import text

        db = SessionLocal()

        # Check if any tables reference removed services
        tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
        result = db.execute(text(tables_query))
        tables = [row[0] for row in result.fetchall()]

        print(f"  📊 Database tables: {len(tables)} found")

        # Check for any service-specific tables
        service_tables = [
            t
            for t in tables
            if any(
                s in t.lower() for s in ["oauth", "textverified_", "pricing_service"]
            )
        ]

        if service_tables:
            print(f"  ⚠️  Service-specific tables found:")
            for table in service_tables:
                print(f"    - {table}")
        else:
            print(f"  ✅ No service-specific tables found")

        db.close()

    except Exception as e:
        print(f"  ❌ Database check error: {e}")


def analyze_feature_completeness():
    """Analyze if any features are broken by removals."""
    print("\n🔍 ANALYZING FEATURE COMPLETENESS:")

    # Key features to test
    features = {
        "SMS Verification": ["textverified_service", "verification"],
        "Pricing System": ["pricing_calculator", "tier_endpoints"],
        "Admin Dashboard": ["admin", "dashboard"],
        "User Authentication": ["auth", "user"],
        "Payment Processing": ["payment", "billing"],
    }

    for feature, keywords in features.items():
        try:
            # Check if feature files exist
            feature_files = []
            for root, dirs, files in os.walk("app"):
                for file in files:
                    if file.endswith(".py") and any(
                        kw in file.lower() for kw in keywords
                    ):
                        feature_files.append(os.path.join(root, file))

            if feature_files:
                print(f"  ✅ {feature}: {len(feature_files)} files found")
            else:
                print(f"  ⚠️  {feature}: No files found")

        except Exception as e:
            print(f"  ❌ {feature}: Error checking - {e}")


def check_template_references():
    """Check if removed templates are referenced anywhere."""
    print("\n🔍 CHECKING TEMPLATE REFERENCES:")

    removed_templates = [
        "verify_stable.html",
        "verify_connected.html",
        "verify_simple.html",
        "verify_modern.html",
    ]

    template_refs = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith((".py", ".html", ".js")):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r") as f:
                        content = f.read()
                        for template in removed_templates:
                            if template in content:
                                template_refs.append((filepath, template))
                except:
                    pass

    if template_refs:
        print(f"  ⚠️  Template references found:")
        for filepath, template in template_refs:
            print(f"    - {filepath}: {template}")
    else:
        print(f"  ✅ No references to removed templates")


def main():
    """Main analysis function."""
    os.chdir("/Users/machine/Desktop/Namaskah. app")

    analyze_removed_files_impact()
    check_main_py_imports()
    test_core_functionality()
    check_database_dependencies()
    analyze_feature_completeness()
    check_template_references()

    print("\n" + "=" * 60)
    print("📋 ANALYSIS COMPLETE")
    print("\nIf any ❌ issues were found above, they need immediate attention.")
    print("If only ✅ results, the cleanup was safe and successful.")


if __name__ == "__main__":
    main()
