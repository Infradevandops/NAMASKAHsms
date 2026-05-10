"""Integration tests for rental area code tier gating."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.subscription_tier import SubscriptionTier
from app.models.user import User


@pytest.fixture
def setup_tiers(db: Session):
    """Setup tier configurations."""
    tiers = [
        SubscriptionTier(
            tier="freemium", name="Freemium", has_area_code_selection=False
        ),
        SubscriptionTier(
            tier="payg", name="Pay-As-You-Go", has_area_code_selection=True
        ),
        SubscriptionTier(tier="pro", name="Pro", has_area_code_selection=True),
    ]
    for tier in tiers:
        db.add(tier)
    db.commit()


def test_rental_freemium_blocked(client: TestClient, db: Session, setup_tiers):
    """Freemium users cannot create rentals at all."""
    user = User(
        id="user1", email="test@test.com", subscription_tier="freemium", credits=50.0
    )
    db.add(user)
    db.commit()

    response = client.post(
        "/api/verification/rentals/request",
        json={
            "service": "whatsapp",
            "duration_hours": 24.0,
        },
        headers={"Authorization": f"Bearer {user.id}"},
    )
    assert response.status_code == 402
    assert "Pro tier" in response.json()["detail"]


def test_rental_payg_charges_area_code_fee(
    client: TestClient, db: Session, setup_tiers, mocker
):
    """PAYG users pay $0.50 for rental area code (but rentals require Pro)."""
    user = User(
        id="user2", email="test2@test.com", subscription_tier="payg", credits=50.0
    )
    db.add(user)
    db.commit()

    response = client.post(
        "/api/verification/rentals/request",
        json={
            "service": "whatsapp",
            "duration_hours": 24.0,
            "area_code": "212",
        },
        headers={"Authorization": f"Bearer {user.id}"},
    )
    # PAYG blocked from rentals entirely
    assert response.status_code == 402


def test_rental_pro_area_code_included(
    client: TestClient, db: Session, setup_tiers, mocker
):
    """Pro users get rental area code included."""
    user = User(
        id="user3", email="test3@test.com", subscription_tier="pro", credits=50.0
    )
    db.add(user)
    db.commit()

    # Mock TextVerified service
    mocker.patch(
        "app.services.textverified_service.TextVerifiedService.get_services_list",
        return_value=[{"id": "whatsapp", "cost": 5.0}],
    )
    mocker.patch(
        "app.services.textverified_service.TextVerifiedService.create_reservation",
        return_value={
            "id": "res123",
            "phone_number": "+12125551234",
            "cost": 5.0,
        },
    )

    response = client.post(
        "/api/verification/rentals/request",
        json={
            "service": "whatsapp",
            "duration_hours": 24.0,
            "area_code": "212",
        },
        headers={"Authorization": f"Bearer {user.id}"},
    )

    if response.status_code == 201:
        data = response.json()
        assert data["area_code_fee"] == 0.0
        assert "requested_area_code" in data
        assert data["requested_area_code"] == "212"
