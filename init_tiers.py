"""Initialize database with subscription tiers"""
from app.core.database import engine
from app.models.base import Base
import app.models
from app.core.database import SessionLocal
from app.models.subscription_tier import SubscriptionTier

# Create all tables
Base.metadata.create_all(bind=engine)
print("✅ Database tables created")

# Create default tiers
db = SessionLocal()
try:
    count = db.query(SubscriptionTier).count()
    if count == 0:
        print("Creating default tiers...")
        tiers = [
            SubscriptionTier(
                tier='freemium',
                name='Freemium',
                description='Get started for free',
                price_monthly=0,
                payment_required=False,
                has_api_access=False,
                has_area_code_selection=False,
                has_isp_filtering=False,
                api_key_limit=0,
                daily_verification_limit=100,
                country_limit=5,
                support_level='community'
            ),
            SubscriptionTier(
                tier='starter',
                name='Starter',
                description='Perfect for growing projects',
                price_monthly=900,
                payment_required=True,
                has_api_access=True,
                has_area_code_selection=True,
                has_isp_filtering=False,
                api_key_limit=5,
                daily_verification_limit=1000,
                country_limit=20,
                support_level='email'
            ),
            SubscriptionTier(
                tier='turbo',
                name='Turbo',
                description='Maximum power and features',
                price_monthly=1399,
                payment_required=True,
                has_api_access=True,
                has_area_code_selection=True,
                has_isp_filtering=True,
                api_key_limit=-1,
                daily_verification_limit=10000,
                country_limit=-1,
                support_level='priority'
            )
        ]
        for tier in tiers:
            db.add(tier)
        db.commit()
        print("✅ Created 3 default tiers")
    else:
        print(f"✅ {count} tiers already exist")
finally:
    db.close()

print("\n🎉 Database initialization complete!")
