#!/usr/bin/env python3
"""Fix subscription tier pricing to match README specifications."""

from app.core.database import SessionLocal
from app.models.subscription_tier import SubscriptionTier

def fix_tier_pricing():
    db = SessionLocal()
    
    try:
        # Update Pro tier: $25/mo with $15 quota
        pro = db.query(SubscriptionTier).filter(SubscriptionTier.tier == "pro").first()
        if pro:
            pro.price_monthly = 2500  # $25.00 in cents
            pro.quota_usd = 15.0
            pro.overage_rate = 0.30
            print(f"✅ Updated Pro tier: ${pro.price_monthly/100}/mo, ${pro.quota_usd} quota")
        
        # Update Custom tier: $35/mo with $25 quota
        custom = db.query(SubscriptionTier).filter(SubscriptionTier.tier == "custom").first()
        if custom:
            custom.price_monthly = 3500  # $35.00 in cents
            custom.quota_usd = 25.0
            custom.overage_rate = 0.20
            print(f"✅ Updated Custom tier: ${custom.price_monthly/100}/mo, ${custom.quota_usd} quota")
        
        db.commit()
        print("\n✅ Tier pricing fixed successfully!")
        
        # Verify
        print("\nCurrent tiers:")
        tiers = db.query(SubscriptionTier).all()
        for tier in tiers:
            price = tier.price_monthly / 100 if tier.price_monthly else 0
            print(f"  {tier.name:15} | ${price:6.2f}/mo | Quota: ${tier.quota_usd:5.2f} | Overage: ${tier.overage_rate:.2f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_tier_pricing()
