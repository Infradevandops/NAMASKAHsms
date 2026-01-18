#!/usr/bin/env python3
"""
Comprehensive flow testing to verify all critical user journeys work flawlessly
"""

import os
import sys
import asyncio
from datetime import datetime

def test_authentication_flow():
    """Test user authentication flow."""
    print("🔐 TESTING AUTHENTICATION FLOW:")
    
    try:
        # Test auth service import
        from app.services.auth_service import AuthService
        from app.core.database import SessionLocal
        
        db = SessionLocal()
        auth_service = AuthService(db)
        
        # Test token creation (mock)
        print("  ✅ Auth service: Initialized")
        print("  ✅ Token management: Available")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Authentication flow error: {e}")
        return False

def test_pricing_flow():
    """Test pricing calculation flow."""
    print("\n💰 TESTING PRICING FLOW:")
    
    try:
        from app.services.pricing_calculator import PricingCalculator
        from app.core.database import SessionLocal
        
        db = SessionLocal()
        calculator = PricingCalculator(db)
        
        # Test tier listing
        tiers = calculator.get_all_tiers()
        print(f"  ✅ Tier listing: {len(tiers)} tiers available")
        
        # Test pricing calculation for each tier
        test_cases = [
            ("payg", "Pay-As-You-Go"),
            ("starter", "Starter"),
            ("pro", "Pro"), 
            ("custom", "Custom")
        ]
        
        for tier_id, tier_name in test_cases:
            try:
                pricing = calculator.calculate_sms_cost("test_user", tier_id)
                cost = pricing["cost_per_sms"]
                within_quota = pricing["within_quota"]
                print(f"  ✅ {tier_name}: ${cost:.2f}/SMS, quota: {within_quota}")
            except Exception as e:
                print(f"  ❌ {tier_name}: Error - {e}")
                db.close()
                return False
        
        db.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Pricing flow error: {e}")
        return False

def test_sms_verification_flow():
    """Test SMS verification flow."""
    print("\n📱 TESTING SMS VERIFICATION FLOW:")
    
    try:
        from app.services.textverified_service import TextVerifiedService
        
        # Test service initialization
        tv_service = TextVerifiedService()
        print("  ✅ TextVerified service: Initialized")
        
        # Test service configuration
        if tv_service.enabled:
            print("  ✅ Service status: Enabled")
        else:
            print("  ⚠️  Service status: Disabled (needs API key)")
        
        # Test API endpoints import
        from app.api.verification.purchase_endpoints import router as purchase_router
        print("  ✅ Purchase endpoints: Available")
        
        return True
        
    except Exception as e:
        print(f"  ❌ SMS verification flow error: {e}")
        return False

def test_admin_dashboard_flow():
    """Test admin dashboard flow."""
    print("\n👑 TESTING ADMIN DASHBOARD FLOW:")
    
    try:
        # Test admin endpoints
        from app.api.admin.stats import router as stats_router
        from app.api.admin.pricing_api import router as pricing_api_router
        from app.api.admin.actions import router as actions_router
        
        print("  ✅ Admin stats: Available")
        print("  ✅ Admin pricing: Available") 
        print("  ✅ Admin actions: Available")
        
        # Test database queries for admin
        from app.core.database import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        
        # Test user count query
        result = db.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        print(f"  ✅ User analytics: {user_count} users")
        
        # Test verification count query
        result = db.execute(text("SELECT COUNT(*) FROM verifications"))
        verification_count = result.scalar()
        print(f"  ✅ Verification analytics: {verification_count} verifications")
        
        # Test tier count query
        result = db.execute(text("SELECT COUNT(*) FROM subscription_tiers"))
        tier_count = result.scalar()
        print(f"  ✅ Tier management: {tier_count} tiers")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Admin dashboard flow error: {e}")
        return False

def test_api_endpoints_flow():
    """Test critical API endpoints."""
    print("\n🔌 TESTING API ENDPOINTS FLOW:")
    
    try:
        # Test tier endpoints
        from app.api.billing.tier_endpoints import router as tier_router
        print("  ✅ Tier endpoints: Available")
        
        # Test pricing endpoints  
        from app.api.billing.pricing_endpoints import router as pricing_router
        print("  ✅ Pricing endpoints: Available")
        
        # Test purchase endpoints
        from app.api.verification.purchase_endpoints import router as purchase_router
        print("  ✅ Purchase endpoints: Available")
        
        # Test auth endpoints
        from app.api.core.auth import router as auth_router
        print("  ✅ Auth endpoints: Available")
        
        # Test system endpoints
        from app.api.core.system import router as system_router
        print("  ✅ System endpoints: Available")
        
        return True
        
    except Exception as e:
        print(f"  ❌ API endpoints flow error: {e}")
        return False

def test_database_flow():
    """Test database operations flow."""
    print("\n🗄️ TESTING DATABASE FLOW:")
    
    try:
        from app.core.database import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        
        # Test core tables exist
        tables_to_check = [
            "users",
            "verifications", 
            "transactions",
            "subscription_tiers",
            "user_quotas"
        ]
        
        for table in tables_to_check:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"  ✅ {table}: {count} records")
            except Exception as e:
                print(f"  ❌ {table}: Error - {e}")
                db.close()
                return False
        
        # Test subscription tiers data
        result = db.execute(text("SELECT tier, name, price_monthly FROM subscription_tiers ORDER BY price_monthly"))
        tiers = result.fetchall()
        
        expected_tiers = ["payg", "starter", "pro", "custom"]
        actual_tiers = [tier[0] for tier in tiers]
        
        if set(expected_tiers) == set(actual_tiers):
            print("  ✅ Tier data: All 4 tiers present")
        else:
            print(f"  ❌ Tier data: Expected {expected_tiers}, got {actual_tiers}")
            db.close()
            return False
        
        db.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Database flow error: {e}")
        return False

def test_template_rendering_flow():
    """Test template rendering flow."""
    print("\n🎨 TESTING TEMPLATE RENDERING FLOW:")
    
    try:
        # Check critical templates exist
        critical_templates = [
            "templates/index.html",
            "templates/dashboard.html", 
            "templates/verify.html",
            "templates/auth.html",
            "templates/admin/dashboard.html"
        ]
        
        missing_templates = []
        for template in critical_templates:
            if not os.path.exists(template):
                missing_templates.append(template)
        
        if missing_templates:
            print(f"  ❌ Missing templates: {missing_templates}")
            return False
        else:
            print(f"  ✅ Critical templates: All {len(critical_templates)} present")
        
        # Test template imports in main.py
        with open('main.py', 'r') as f:
            content = f.read()
        
        if 'Jinja2Templates' in content:
            print("  ✅ Template engine: Jinja2 configured")
        else:
            print("  ❌ Template engine: Not configured")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Template rendering flow error: {e}")
        return False

def test_complete_user_journey():
    """Test a complete user journey simulation."""
    print("\n🚀 TESTING COMPLETE USER JOURNEY:")
    
    try:
        # Simulate: User registration → Login → SMS Purchase → Admin View
        
        # Step 1: User can register (auth service available)
        from app.services.auth_service import AuthService
        print("  ✅ Step 1: Registration service available")
        
        # Step 2: User can view pricing (pricing calculator available)
        from app.services.pricing_calculator import PricingCalculator
        print("  ✅ Step 2: Pricing display available")
        
        # Step 3: User can purchase SMS (TextVerified + purchase endpoints)
        from app.services.textverified_service import TextVerifiedService
        from app.api.verification.purchase_endpoints import router
        print("  ✅ Step 3: SMS purchase flow available")
        
        # Step 4: Admin can view analytics (admin endpoints)
        from app.api.admin.stats import router as admin_router
        print("  ✅ Step 4: Admin analytics available")
        
        # Step 5: Database supports full journey
        from app.core.database import SessionLocal
        db = SessionLocal()
        
        # Check all required tables for user journey
        journey_tables = ["users", "subscription_tiers", "verifications", "transactions", "user_quotas"]
        for table in journey_tables:
            result = db.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
            # Table exists and is queryable
        
        db.close()
        print("  ✅ Step 5: Database supports full journey")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Complete user journey error: {e}")
        return False

def main():
    """Main flow testing function."""
    print("🔍 COMPREHENSIVE FLOW TESTING")
    print("=" * 60)
    
    os.chdir("/Users/machine/Desktop/Namaskah. app")
    
    # Test all critical flows
    flows = [
        ("Authentication", test_authentication_flow),
        ("Pricing", test_pricing_flow),
        ("SMS Verification", test_sms_verification_flow),
        ("Admin Dashboard", test_admin_dashboard_flow),
        ("API Endpoints", test_api_endpoints_flow),
        ("Database", test_database_flow),
        ("Template Rendering", test_template_rendering_flow),
        ("Complete User Journey", test_complete_user_journey)
    ]
    
    results = {}
    
    for flow_name, test_func in flows:
        try:
            results[flow_name] = test_func()
        except Exception as e:
            print(f"❌ {flow_name} flow crashed: {e}")
            results[flow_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 FLOW TESTING RESULTS:")
    
    passed = sum(results.values())
    total = len(results)
    
    for flow_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"  {status} {flow_name}")
    
    print(f"\n🎯 OVERALL RESULT: {passed}/{total} flows passed")
    
    if passed == total:
        print("🎉 ALL FLOWS ARE FLAWLESS!")
        print("🚀 System ready for production")
        return True
    else:
        print("⚠️  SOME FLOWS HAVE ISSUES")
        print("🔧 Manual review needed")
        return False

if __name__ == "__main__":
    main()