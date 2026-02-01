"""Clean test user balances and ensure data integrity."""


import os
import sys
from app.core.config import get_settings
from app.core.database import engine
from app.models.balance_transaction import BalanceTransaction
from app.models.user import User
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


settings = get_settings()

Session = sessionmaker(bind=engine)
db = Session()


def clean_test_balances():

    """Reset test user balances to 0 (excluding admin)."""
    test_users = (
        db.query(User)
        .filter(
            (User.email.like("%test%"))
            | (User.email.like("%demo%"))
            | (User.email.like("%example%"))
        )
        .filter(~User.is_admin)  # Don't reset admin balance
        .all()
    )

for user in test_users:
        print(f"Resetting balance for {user.email}: ${user.credits} -> $0.00")
        user.credits = 0.0

    db.commit()
    print(f"✓ Reset {len(test_users)} test user balances (admin excluded)")


def validate_balances():

    """Ensure all balances match transaction history."""
    users = db.query(User).all()
    issues = 0

for user in users:
        transactions = db.query(BalanceTransaction).filter_by(user_id=user.id).all()
        calculated_balance = sum(t.amount for t in transactions)

if abs(user.credits - calculated_balance) > 0.01:
            print(f"⚠ Balance mismatch for {user.email}:")
            print(f"  Database: ${user.credits}")
            print(f"  Calculated: ${calculated_balance}")
            print("  Fixing...")
            user.credits = calculated_balance
            issues += 1

    db.commit()
if issues > 0:
        print(f"✓ Fixed {issues} balance mismatches")
else:
        print("✓ All balances validated - no issues found")


if __name__ == "__main__":
    print("Starting balance cleanup...")
    clean_test_balances()
    validate_balances()
    print("Done!")
