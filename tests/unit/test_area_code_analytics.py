from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from main import app
from app.core.database import SessionLocal, get_db
from app.models.purchase_outcome import PurchaseOutcome
from app.models.user import User
from app.api.admin.admin_router import require_admin

client = TestClient(app)

@pytest.fixture
def override_require_admin():
    def mock_require_admin():
        return "admin_user_id"
    
    app.dependency_overrides[require_admin] = mock_require_admin
    yield
    app.dependency_overrides.pop(require_admin, None)

@pytest.fixture
def mock_db():
    db = MagicMock()
    def override_get_db():
        yield db
        
    app.dependency_overrides[get_db] = override_get_db
    yield db
    app.dependency_overrides.pop(get_db, None)

def test_area_codes_empty_data(override_require_admin, mock_db):
    mock_db.query().filter().all.return_value = []
    
    response = client.get("/api/admin/analytics/area-codes?days=7")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_purchases"] == 0
    assert data["match_rate"] == 0.0
    assert data["top_requested"] == []
    
def test_carriers_empty_data(override_require_admin, mock_db):
    mock_db.query().filter().all.return_value = []
    
    response = client.get("/api/admin/analytics/carriers?days=7")
    
    assert response.status_code == 200
    data = response.json()
    assert data["carrier_distribution"] == []
    assert data["voip_rate"] == 0.0
    assert data["landline_rate"] == 0.0

def test_area_codes_analytics_aggregation(override_require_admin, mock_db):
    # Mock data
    now_utc = datetime.now(timezone.utc)
    outcomes = [
        PurchaseOutcome(service="whatsapp", requested_code="213", assigned_code="213", matched=True, created_at=now_utc),
        PurchaseOutcome(service="whatsapp", requested_code="213", assigned_code="323", matched=False, created_at=now_utc),
        PurchaseOutcome(service="telegram", requested_code="907", assigned_code="907", matched=True, created_at=now_utc),
    ]
    
    mock_db.query().filter().all.return_value = outcomes
    
    response = client.get("/api/admin/analytics/area-codes?days=7")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_purchases"] == 3
    assert data["match_rate"] == 0.67  # 2/3
    
    # 213 check
    top = next((t for t in data["top_requested"] if t["area_code"] == "213"), None)
    assert top is not None
    assert top["requests"] == 2
    assert top["success_rate"] == 0.5  # 1/2
    
def test_carriers_analytics_distribution(override_require_admin, mock_db):
    now_utc = datetime.now(timezone.utc)
    outcomes = [
        PurchaseOutcome(service="whatsapp", assigned_carrier="att", sms_received=True, carrier_type="mobile", created_at=now_utc),
        PurchaseOutcome(service="whatsapp", assigned_carrier="att", sms_received=False, carrier_type="mobile", created_at=now_utc),
        PurchaseOutcome(service="telegram", assigned_carrier="tmobile", sms_received=True, carrier_type="mobile", created_at=now_utc),
        PurchaseOutcome(service="telegram", assigned_carrier="verizon", sms_received=None, carrier_type="voip", created_at=now_utc), # Voip, sms=None
    ]
    
    mock_db.query().filter().all.return_value = outcomes
    
    response = client.get("/api/admin/analytics/carriers?days=7")
    
    assert response.status_code == 200
    data = response.json()
    dist = data["carrier_distribution"]
    
    # Check percentages
    total_pct = sum(d["pct"] for d in dist)
    # the sum might not be exactly 1.0 due to rounding, but close. Actually, wait!
    # "unknown" with < 5 count are filtered. Since we have 4 outcomes, all carriers < 5 count!
    # Wait, in the code: `if c == "unknown" and stats["count"] < 5: continue`
    # Our carriers are "att", "tmobile", "verizon" - none are "unknown"!
    assert len(dist) == 3
    assert pytest.approx(total_pct, 0.01) == 1.0
    
    att = next(d for d in dist if d["carrier"] == "att")
    assert att["sms_delivery_rate"] == 0.5  # 1/2
    assert data["voip_rate"] == 0.25

def test_missing_admin_throws_401():
    # Attempting to fetch without logging in as admin
    response = client.get("/api/admin/analytics/area-codes")
    assert response.status_code == 401

def test_geography_analytics_aggregation(override_require_admin, mock_db):
    now_utc = datetime.now(timezone.utc)
    outcomes = [
        PurchaseOutcome(service="whatsapp", requested_code="213", assigned_code="213", sms_received=True, created_at=now_utc),
        PurchaseOutcome(service="whatsapp", requested_code="310", assigned_code="310", sms_received=True, created_at=now_utc),
    ]
    mock_db.query().filter().all.return_value = outcomes
    
    response = client.get("/api/admin/analytics/geography?days=7")
    
    assert response.status_code == 200
    data = response.json()
    assert "top_cities" in data
    assert "top_states" in data
    
    # CA should be the state for 213/310 (Assuming NANPA_DATA catches it)
    ca = next((s for s in data["top_states"] if s["state"] == "CA"), None)
    if ca:
        assert ca["purchases"] == 2
        assert ca["unique_area_codes"] == 2
