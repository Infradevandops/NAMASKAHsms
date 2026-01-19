import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.user import User
from app.models.subscription_tier import SubscriptionTier

print("Testing database setup...")
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

try:
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

    session = TestingSessionLocal()
    print("Seeding tiers...")
    tiers = [
        SubscriptionTier(tier="freemium", name="Freemium", price_monthly=0),
        SubscriptionTier(tier="pro", name="Pro", price_monthly=2500),
    ]
    for tier in tiers:
        session.add(tier)
    session.commit()
    print("Tiers seeded.")

    print("Creating user...")
    user = User(
        email="test@example.com", password_hash="hash", subscription_tier="freemium"
    )
    session.add(user)
    session.commit()
    print(f"User created with ID: {user.id}")

    session.close()
    print("Debug script finished successfullly.")
except Exception as e:
    print(f"Error during setup: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
