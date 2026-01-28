"""Integration tests for database operations."""

import pytest
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.verification import Verification


@pytest.mark.integration
def test_create_user(db: Session):
    """Test creating a user."""
    user = User(
        id="test-user-1",
        email="test@example.com",
        phone_number="+1234567890",
        password_hash="hashed",
        is_verified=True,
        credits=100.0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    assert user.id == "test-user-1"
    assert user.email == "test@example.com"
    assert user.credits == 100.0


@pytest.mark.integration
def test_create_verification(db: Session, test_user_id: str):
    """Test creating a verification."""
    verification = Verification(
        user_id=test_user_id,
        service_name="telegram",
        phone_number="+1234567890",
        capability="sms",
        status="pending",
        cost=0.50,
        provider="textverified",
        activation_id="act-123",
    )
    db.add(verification)
    db.commit()
    db.refresh(verification)
    
    assert verification.service_name == "telegram"
    assert verification.status == "pending"
    assert verification.cost == 0.50


@pytest.mark.integration
def test_query_user_verifications(db: Session, test_user_id: str):
    """Test querying user verifications."""
    # Create test user
    user = User(
        id=test_user_id,
        email="test@example.com",
        phone_number="+1234567890",
        password_hash="hashed",
        is_verified=True,
        credits=100.0,
    )
    db.add(user)
    db.commit()
    
    # Create verifications
    for i in range(3):
        verification = Verification(
            user_id=test_user_id,
            service_name=f"service-{i}",
            phone_number=f"+123456789{i}",
            capability="sms",
            status="pending",
            cost=0.50,
            provider="textverified",
            activation_id=f"act-{i}",
        )
        db.add(verification)
    db.commit()
    
    # Query verifications
    verifications = db.query(Verification).filter(
        Verification.user_id == test_user_id
    ).all()
    
    assert len(verifications) == 3
    assert all(v.user_id == test_user_id for v in verifications)
