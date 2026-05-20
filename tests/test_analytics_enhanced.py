from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.verification import Verification
from tests.conftest import create_test_token


def test_get_analytics_summary_empty(client, regular_user):
    """Test analytics summary with no data."""
    token = create_test_token(regular_user.id, regular_user.email)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/analytics/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_verifications"] == 0
    assert data["total_spent"] == 0
    assert len(data["daily_verifications"]) > 0


def test_get_analytics_summary_with_data(client, db: Session, regular_user):
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

    token = create_test_token(regular_user.id, regular_user.email)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/analytics/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["total_verifications"] == 2
    assert data["successful_verifications"] == 1
    assert data["failed_verifications"] == 1
    assert data["total_spent"] == 1.50
    assert len(data["top_services"]) > 0
    assert data["top_services"][0]["name"] in ["whatsapp", "telegram"]


def test_analytics_date_filter(client, db: Session, regular_user):
    """Test analytics date filtering with proper isolation."""
    # Clean state - use nested transaction for isolation
    from sqlalchemy import text
    
    # Delete any existing verifications for this user
    db.execute(text("DELETE FROM verifications WHERE user_id = :user_id"), {"user_id": regular_user.id})
    db.commit()
    
    # Add old verification (outside default 30-day range)
    old_date = datetime.utcnow() - timedelta(days=60)
    v_old = Verification(
        user_id=regular_user.id,
        phone_number="+1111111111",
        service_name="facebook",
        status="completed",
        cost=0.0,
    )
    # Manually set created_at AFTER adding to session
    db.add(v_old)
    db.flush()  # Flush to get ID but don't commit yet
    
    # Update created_at directly in DB to bypass any ORM defaults
    db.execute(
        text("UPDATE verifications SET created_at = :created_at WHERE id = :id"),
        {"created_at": old_date, "id": v_old.id}
    )
    db.commit()
    db.refresh(v_old)

    token = create_test_token(regular_user.id, regular_user.email)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Query default range (30 days) - should not see old verification
    response = client.get("/api/analytics/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_verifications"] == 0, \
        f"Expected 0 verifications in last 30 days, got {data['total_verifications']}"

    # Query extended range (90 days) - should see old verification
    from_date = (datetime.utcnow() - timedelta(days=90)).isoformat()
    response = client.get(
        f"/api/analytics/summary?from_date={from_date}", headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_verifications"] == 1, \
        f"Expected 1 verification in last 90 days, got {data['total_verifications']}"


def test_real_time_stats(client, regular_user):
    """Test real-time stats endpoint."""
    token = create_test_token(regular_user.id, regular_user.email)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/analytics/real-time-stats", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "balance" in data
    assert "pending_verifications" in data


def test_status_updates(client, regular_user):
    """Test status updates endpoint."""
    token = create_test_token(regular_user.id, regular_user.email)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/analytics/status-updates", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "updates" in data
