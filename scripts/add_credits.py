#!/usr/bin/env python3
"""Add credits to user account for testing."""

import sys
import os
from decimal import Decimal

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.user import User


def add_credits(email: str, amount: float):
    """Add credits to user account."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ User {email} not found")
            return False

        old_balance = float(user.credits)
        user.credits = Decimal(str(float(user.credits) + amount))
        db.commit()

        print(f"✅ Added ${amount:.2f} to {email}")
        print(f"   Old balance: ${old_balance:.2f}")
        print(f"   New balance: ${float(user.credits):.2f}")
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/add_credits.py <email> <amount>")
        print("Example: python scripts/add_credits.py user@example.com 50")
        sys.exit(1)

    email = sys.argv[1]
    amount = float(sys.argv[2])

    add_credits(email, amount)
