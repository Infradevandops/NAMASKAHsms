

from sqlalchemy.orm import Session
from app.models.user import User

def test_get_referral_stats(client, auth_headers, regular_user):

    """Test getting referral stats."""
    response = client.get("/api/referrals/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "referral_code" in data
    assert "referral_link" in data
    assert data["total_referred"] >= 0


def test_list_referrals_empty(client, auth_headers):

    """Test listing referrals when none exist."""
    response = client.get("/api/referrals/list", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()["data"]) == 0


def test_list_referrals_with_data(client, auth_headers, db: Session, regular_user):

    """Test listing referrals when they exist."""
    # Create a referred user
    referred = User(
        email="referred@example.com",
        password_hash="...",
        referred_by=regular_user.id,
        subscription_tier="freemium",
    )
    db.add(referred)
    db.commit()

    response = client.get("/api/referrals/list", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["email"].startswith("ref")  # Masked email