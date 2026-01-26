from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.verification import Verification


def test_get_analytics_summary_empty(client, auth_headers):
    """Test analytics summary with no data."""
    response = client.get("/api/analytics/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_verifications"] == 0
    assert data["total_spent"] == 0
    assert len(data["daily_verifications"]) > 0


def test_get_analytics_summary_with_data(client, auth_headers, db: Session, regular_user):
    """Test analytics summary with verifications and transactions."""
    # Add verifications
    v1 = Verification(
        user_id=regular_user.id,
        phone_number="+1234567890",
        service_name="whatsapp",
        status="completed",
        country="US",
        cost=1.50,
    )
    v2 = Verification(
        user_id=regular_user.id,
        phone_number="+1987654321",
        service_name="telegram",
        status="failed",
        country="UK",
        cost=0.50,
    )
    db.add(v1)
    db.add(v2)

    # Add transaction
    t1 = Transaction(
        user_id=regular_user.id,
        amount=-1.50,
        type="SMS Verification",
        description="Verification fee",
    )
    db.add(t1)
    db.commit()

    response = client.get("/api/analytics/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["total_verifications"] == 2
    assert data["successful_verifications"] == 1
    assert data["failed_verifications"] == 1
    assert data["total_spent"] == 1.50
    assert len(data["top_services"]) > 0
    assert data["top_services"][0]["name"] in ["whatsapp", "telegram"]


def test_analytics_date_filter(client, auth_headers, db: Session, regular_user):
    """Test analytics date filtering."""
    # Add old verification
    old_date = datetime.utcnow() - timedelta(days=60)
    v_old = Verification(
        user_id=regular_user.id,
        phone_number="+1111111111",
        service_name="facebook",
        status="completed",
        cost=0.0,
    )
    v_old.created_at = old_date
    db.add(v_old)
    db.commit()

    # Query default range (30 days) - should not see old one
    response = client.get("/api/analytics/summary", headers=auth_headers)
    data = response.json()
    assert data["total_verifications"] == 0

    # Query extended range
    from_date = (datetime.utcnow() - timedelta(days=90)).isoformat()
    response = client.get(f"/api/analytics/summary?from_date={from_date}", headers=auth_headers)
    data = response.json()
    assert data["total_verifications"] == 1


def test_real_time_stats(client, auth_headers):
    """Test real-time stats endpoint."""
    response = client.get("/api/analytics/real-time-stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "balance" in data
    assert "pending_verifications" in data


def test_status_updates(client, auth_headers):
    """Test status updates endpoint."""
    response = client.get("/api/analytics/status-updates", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "updates" in data
