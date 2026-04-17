"""
Integration tests for the area code check endpoint.

score_availability now opens SessionLocal internally, so we patch
SessionLocal to reuse the same test db_session that we seed with data.
"""
import pytest
from app.models.purchase_outcome import PurchaseOutcome
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock, MagicMock


@pytest.fixture(autouse=True)
def mock_cache_and_tv(db_session):
    """Clean purchase_outcomes, stub cache misses, stub TextVerified list."""
    db_session.query(PurchaseOutcome).delete()
    db_session.commit()

    with patch("app.api.verification.area_code_endpoints.cache.get", new_callable=AsyncMock) as m_get, \
         patch("app.api.verification.area_code_endpoints.cache.set", new_callable=AsyncMock), \
         patch("app.services.purchase_intelligence.cache.get", new_callable=AsyncMock) as pi_get, \
         patch("app.services.purchase_intelligence.cache.set", new_callable=AsyncMock), \
         patch("app.api.verification.area_code_endpoints._tv.get_area_codes_list", new_callable=AsyncMock) as m_tv:

        m_get.return_value = {"area_codes": [213, 310, 323, 714]}
        pi_get.return_value = None         # force live computation
        m_tv.return_value = [213, 310, 323, 714]

        yield {"get": m_get, "tv": m_tv}


def _patch_session(db_session):
    """Return a context manager that routes SessionLocal() → db_session."""
    return patch(
        "app.services.purchase_intelligence.SessionLocal",
        return_value=db_session
    )


@pytest.mark.asyncio
async def test_area_code_check_unsupported(authenticated_client):
    """999 is not in NANPA → 400 Unknown area code."""
    response = authenticated_client.get("/api/area-codes/check?service=whatsapp&area_code=999")
    assert response.status_code == 400
    assert "Unknown area code" in str(response.json())


@pytest.mark.asyncio
async def test_area_code_check_unknown_to_tv(authenticated_client, mock_cache_and_tv):
    """Area code in NANPA but not in provider list → 400 not supported."""
    mock_cache_and_tv["get"].return_value = {"area_codes": []}
    mock_cache_and_tv["tv"].return_value = []

    response = authenticated_client.get("/api/area-codes/check?service=whatsapp&area_code=212")
    assert response.status_code == 400
    assert "Area code not supported" in str(response.json())


@pytest.mark.asyncio
async def test_area_code_check_available(authenticated_client, db_session, mock_cache_and_tv):
    """5 matches for 213+whatsapp → status=available."""
    mock_cache_and_tv["get"].return_value = {"area_codes": [213, 310, 323]}

    now = datetime.now(timezone.utc)
    for _ in range(5):
        db_session.add(PurchaseOutcome(
            service="whatsapp",
            requested_code="213",
            assigned_code="213",
            matched=True,
            created_at=now - timedelta(hours=1)
        ))
    db_session.commit()

    with _patch_session(db_session):
        response = authenticated_client.get("/api/area-codes/check?service=whatsapp&area_code=213")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "available"
    assert "is available" in data["message"]


@pytest.mark.asyncio
async def test_area_code_check_unavailable_with_alternatives(authenticated_client, db_session, mock_cache_and_tv):
    """5 mismatches for 213+whatsapp → status=unavailable, alternatives include 323."""
    mock_cache_and_tv["get"].return_value = {"area_codes": [213, 323, 714]}

    now = datetime.now(timezone.utc)
    for _ in range(5):
        db_session.add(PurchaseOutcome(
            service="whatsapp",
            requested_code="213",
            assigned_code="323",
            matched=False,
            created_at=now - timedelta(hours=1)
        ))
    db_session.commit()

    with _patch_session(db_session):
        response = authenticated_client.get("/api/area-codes/check?service=whatsapp&area_code=213")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unavailable"
    assert "is not available" in data["message"]
    assert "alternatives" in data
    assert len(data["alternatives"]) > 0

    alts = [a["area_code"] for a in data["alternatives"]]
    assert "323" in alts
