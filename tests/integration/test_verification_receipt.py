"""Integration test for verification receipt accuracy."""

import os
import sys
import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import SessionLocal
from app.models.verification import Verification
from app.models.user import User

def test_verification_receipt_fields():
    """Test that all receipt fields are present in the database after purchase."""
    db = SessionLocal()
    try:
        # Create a test user if not exists
        user = db.query(User).filter(User.email == "test_receipt@example.com").first()
        if not user:
            user = User(
                email="test_receipt@example.com",
                credits=100.0,
                subscription_tier="payg"
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Create a test verification with all new fields
        v = Verification(
            user_id=str(user.id),
            service_name="telegram",
            phone_number="+14155550199",
            country="US",
            capability="sms",
            status="completed",
            cost=2.75,
            requested_area_code="212",
            requested_carrier="verizon",
            assigned_area_code="415",
            assigned_carrier="T-Mobile",
            fallback_applied=True,
            same_state_fallback=False,
            created_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc)
        )
        db.add(v)
        db.commit()
        db.refresh(v)

        # Verify fields
        assert v.assigned_area_code == "415"
        assert v.assigned_carrier == "T-Mobile"
        assert v.fallback_applied is True
        assert v.same_state_fallback is False
        assert v.requested_area_code == "212"
        assert v.requested_carrier == "verizon"
        
        print(f"✅ Integration test passed: Verification {v.id} stores all receipt fields.")
        
        # Cleanup
        db.delete(v)
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    test_verification_receipt_fields()
