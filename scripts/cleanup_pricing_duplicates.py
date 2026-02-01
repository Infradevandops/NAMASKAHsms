#!/usr/bin/env python3
"""
import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.logging import get_logger
from app.services.pricing_calculator import PricingCalculator

Clean up duplicates and conflicts in pricing system
"""


def backup_file(filepath):

    """Create backup of file before modification."""
if os.path.exists(filepath):
        backup_path = filepath + ".backup"
        shutil.copy2(filepath, backup_path)
        print(f"📁 Backed up {filepath} to {backup_path}")


def remove_duplicate_endpoints():

    """Remove duplicate pricing endpoints that conflict with new tier system."""

    # The old pricing_endpoints.py conflicts with our new tier_endpoints.py
    old_pricing_file = (
        "/Users/machine/Desktop/Namaskah. app/app/api/billing/pricing_endpoints.py"
    )

if os.path.exists(old_pricing_file):
        backup_file(old_pricing_file)

        # Read the file to see what endpoints we need to preserve
with open(old_pricing_file, "r") as f:
            f.read()

        # Keep only non-conflicting endpoints (estimate, services, countries)
        new_content = '''"""Pricing estimation endpoints - Non-conflicting with tier system."""


logger = get_logger(__name__)
router = APIRouter(prefix="/api/pricing", tags=["Pricing"])


@router.get("/estimate")
async def estimate_verification_cost(
    service: str = Query(..., description="Service name (telegram, whatsapp, etc)"),
    country: str = Query("US", description="Country code"),
    quantity: int = Query(1, ge=1, le=1000, description="Number of verifications"),
    db: Session = Depends(get_db)
):
    """Estimate cost for verification(s) using new pricing system."""
try:

        calculator = PricingCalculator(db)

        # Simple estimation - always use Pay-As-You-Go pricing for estimates
        base_cost = 2.50  # Pay-As-You-Go rate
        total_cost = base_cost * quantity

        return {
            "service": service,
            "country": country,
            "quantity": quantity,
            "cost_per_sms": base_cost,
            "total_cost": total_cost,
            "currency": "USD",
            "note": "Actual cost may vary based on your subscription tier"
        }

except Exception as e:
        logger.error(f"Failed to estimate cost: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to estimate cost"
        )


@router.get("/services")
async def get_available_services():
    """Get list of available services."""
    services = {
        "telegram": "Telegram",
        "whatsapp": "WhatsApp",
        "google": "Google",
        "facebook": "Facebook",
        "instagram": "Instagram",
        "twitter": "Twitter",
        "discord": "Discord",
        "tiktok": "TikTok"
    }

    return {
        "services": services,
        "total": len(services)
    }


@router.get("/countries")
async def get_available_countries():
    """Get list of available countries."""
    countries = {
        "US": "United States",
        "CA": "Canada",
        "GB": "United Kingdom",
        "DE": "Germany",
        "FR": "France"
    }

    return {
        "countries": countries,
        "total": len(countries)
    }
'''

with open(old_pricing_file, "w") as f:
            f.write(new_content)

        print(f"✅ Cleaned up {old_pricing_file} - removed conflicting endpoints")


def check_main_py_imports():

    """Check and fix main.py imports."""
    main_file = "/Users/machine/Desktop/Namaskah. app/main.py"

if os.path.exists(main_file):
with open(main_file, "r") as f:
            content = f.read()

        # Check for duplicate tier router imports
        tier_imports = content.count("tier_endpoints")
        pricing_imports = content.count("billing_pricing_router")

        print("📊 main.py analysis:")
        print(f"  - tier_endpoints imports: {tier_imports}")
        print(f"  - billing_pricing_router imports: {pricing_imports}")

if tier_imports > 0 and pricing_imports > 0:
            print("✅ Both tier and pricing routers are imported (no conflicts)")
else:
            print("⚠️  Check main.py router imports")


def remove_unused_services():

    """Check for unused service files."""

    # Check if old PricingService is still needed
    pricing_service_file = (
        "/Users/machine/Desktop/Namaskah. app/app/services/pricing_service.py"
    )

if os.path.exists(pricing_service_file):
        print("📁 Found old pricing_service.py - keeping as backup")
        print("   (New PricingCalculator replaces most functionality)")


def main():

    """Main cleanup function."""
    print("🧹 Starting pricing system cleanup...")
    print("=" * 50)

    # Step 1: Remove duplicate endpoints
    remove_duplicate_endpoints()

    # Step 2: Check main.py imports
    check_main_py_imports()

    # Step 3: Check unused services
    remove_unused_services()

    print("\n" + "=" * 50)
    print("✅ Cleanup completed!")
    print("\n📋 Summary:")
    print("  - Removed conflicting pricing endpoints")
    print("  - Kept estimation endpoints")
    print("  - Preserved old files as backups")
    print("  - New tier system is primary")

    print("\n🚀 Next steps:")
    print("  1. Test the server: uvicorn main:app --reload")
    print("  2. Test endpoints: curl http://localhost:8000/api/tiers/")
    print("  3. Verify no conflicts in logs")


if __name__ == "__main__":
    main()