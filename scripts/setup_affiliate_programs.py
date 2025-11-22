#!/usr/bin/env python3
"""Setup affiliate programs in database."""

import os
import sys

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.affiliate import AffiliateProgram

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def setup_affiliate_programs():
    """Initialize affiliate programs in database."""
    db = next(get_db())

    # Check if programs already exist
    existing = db.query(AffiliateProgram).first()
    if existing:
        print("Affiliate programs already exist. Skipping setup.")
        return

    # Create Individual Referral Program
    referral_program = AffiliateProgram(
        name="Individual Referral Program",
        program_type="referral",
        commission_rate=0.10,  # 10%
        tier_requirements={
            "min_referrals": 0,
            "min_revenue": 0
        },
        features={
            "sms_verification": True,
            "whatsapp_integration": True,
            "payment_processing": True,
            "api_access": True,
            "real_time_tracking": True,
            "monthly_payouts": True,
            "marketing_materials": True,
            "support_24_7": True
        },
        is_active=True
    )

    # Create Enterprise Affiliate Program
    enterprise_program = AffiliateProgram(
        name="Enterprise Affiliate Program",
        program_type="enterprise",
        commission_rate=0.25,  # 25% (can go up to 30% with bonuses)
        tier_requirements={
            "min_monthly_revenue": 1000,
            "min_referrals": 10
        },
        features={
            "white_label_solutions": True,
            "reseller_programs": True,
            "custom_integration_support": True,
            "dedicated_account_manager": True,
            "volume_discounts": True,
            "priority_support": True,
            "custom_branding": True,
            "multi_domain_management": True,
            "custom_pricing_negotiations": True,
            "quarterly_business_reviews": True,
            "performance_bonuses": True,
            "revenue_sharing_up_to_30": True
        },
        is_active=True
    )

    # Add to database
    db.add(referral_program)
    db.add(enterprise_program)
    db.commit()

    print("✅ Affiliate programs created successfully!")
    print(f"- {referral_program.name}: {referral_program.commission_rate*100}% commission")
    print(f"- {enterprise_program.name}: {enterprise_program.commission_rate*100}% commission")


if __name__ == "__main__":
    setup_affiliate_programs()
