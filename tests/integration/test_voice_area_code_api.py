"""Integration tests for voice verification area code tier gating."""

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


def test_voice_freemium_blocked_from_area_code(
    client: TestClient, db: Session, setup_tiers
):
    """Freemium users cannot request voice with area code."""
    user = User(
        id="user1", email="test@test.com", subscription_tier="freemium", credits=10.0
    )
    db.add(user)
    db.commit()

    response = client.post(
        "/api/verification/request",
        json={
            "service": "whatsapp",
            "country": "US",
            "capability": "voice",
            "area_codes": ["212"],
        },
        headers={"Authorization": f"Bearer {user.id}"},
    )
    assert response.status_code == 402
    assert "Area code" in response.json()["detail"]


def test_voice_payg_charges_area_code_fee(
    client: TestClient, db: Session, setup_tiers, mocker
):
    """PAYG users pay $0.25 for voice area code."""
    user = User(
        id="user2", email="test2@test.com", subscription_tier="payg", credits=10.0
    )
    db.add(user)
    db.commit()

    # Mock TextVerified service
    mocker.patch(
        "app.api.verification.purchase_endpoints._get_provider_price", return_value=1.0
    )
    mocker.patch(
        "app.services.providers.provider_router.ProviderRouter.purchase_with_failover"
    )

    response = client.post(
        "/api/verification/request",
        json={
            "service": "whatsapp",
            "country": "US",
            "capability": "voice",
            "area_codes": ["212"],
        },
        headers={"Authorization": f"Bearer {user.id}"},
    )

    if response.status_code == 201:
        data = response.json()
        assert data["area_code_fee"] == 0.25
        assert data["cost"] > data["base_cost"]


def test_voice_pro_area_code_included(
    client: TestClient, db: Session, setup_tiers, mocker
):
    """Pro users get voice area code included."""
    user = User(
        id="user3", email="test3@test.com", subscription_tier="pro", credits=10.0
    )
    db.add(user)
    db.commit()

    mocker.patch(
        "app.api.verification.purchase_endpoints._get_provider_price", return_value=1.0
    )
    mocker.patch(
        "app.services.providers.provider_router.ProviderRouter.purchase_with_failover"
    )

    response = client.post(
        "/api/verification/request",
        json={
            "service": "whatsapp",
            "country": "US",
            "capability": "voice",
            "area_codes": ["212"],
        },
        headers={"Authorization": f"Bearer {user.id}"},
    )

    if response.status_code == 201:
        data = response.json()
        assert data["area_code_fee"] == 0.0
