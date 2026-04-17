"""
Unit tests for PurchaseIntelligenceService.score_availability.

The service now opens its own SessionLocal internally (no db argument).
We patch SessionLocal so the test-inserted rows are visible to the service.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta, timezone
from app.services.purchase_intelligence import PurchaseIntelligenceService, AvailabilityScore
from app.models.purchase_outcome import PurchaseOutcome


def _make_outcome(**kwargs):
    """Helper: default keyword args for PurchaseOutcome rows."""
    return PurchaseOutcome(**kwargs)


@pytest.fixture(autouse=True)
def patch_cache():
    """Always bypass cache in unit tests so we exercise live DB logic."""
    with patch("app.services.purchase_intelligence.cache.get", new_callable=AsyncMock) as m_get, \
         patch("app.services.purchase_intelligence.cache.set", new_callable=AsyncMock):
        m_get.return_value = None  # cache miss → compute from DB
        yield


def _mock_session_local(rows):
    """Return a patcher that makes SessionLocal() yield a mock session with preset rows."""
    mock_session = MagicMock()
    mock_query = mock_session.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.all.return_value = rows
    return patch("app.services.purchase_intelligence.SessionLocal", return_value=mock_session)


@pytest.mark.asyncio
async def test_score_availability_no_data():
    """No history → unknown, zero confidence."""
    with _mock_session_local([]):
        score = await PurchaseIntelligenceService.score_availability("whatsapp", "213")
    assert score.available is None
    assert score.confidence == 0.0
    assert score.sample_size == 0


@pytest.mark.asyncio
async def test_score_availability_high_success():
    """5 matched outcomes → available=True, confidence=0.6, rate=1.0."""
    now = datetime.now(timezone.utc)
    rows = [
        _make_outcome(service="whatsapp", assigned_code="213", requested_code="213",
                      matched=True, created_at=now - timedelta(days=i))
        for i in range(5)
    ]
    with _mock_session_local(rows):
        score = await PurchaseIntelligenceService.score_availability("whatsapp", "213")
    assert score.available is True
    assert score.confidence == 0.6   # 5 samples → 0.6
    assert score.success_rate == 1.0


@pytest.mark.asyncio
async def test_score_availability_high_failures():
    """5 mismatched outcomes → available=False, confidence=0.6, rate=0.0."""
    now = datetime.now(timezone.utc)
    rows = [
        _make_outcome(service="whatsapp", requested_code="213", assigned_code="469",
                      matched=False, created_at=now - timedelta(days=i))
        for i in range(5)
    ]
    with _mock_session_local(rows):
        score = await PurchaseIntelligenceService.score_availability("whatsapp", "213")
    assert score.available is False
    assert score.confidence == 0.6
    assert score.success_rate == 0.0


@pytest.mark.asyncio
async def test_score_availability_mixed():
    """2 success + 2 failures (not recent) → rate 0.5 → available=None (ambiguous)."""
    now = datetime.now(timezone.utc)
    rows = [
        _make_outcome(service="whatsapp", assigned_code="213", requested_code="213",
                      matched=True, created_at=now - timedelta(hours=3)),
        _make_outcome(service="whatsapp", assigned_code="213", requested_code="213",
                      matched=True, created_at=now - timedelta(hours=4)),
        _make_outcome(service="whatsapp", requested_code="213", assigned_code="469",
                      matched=False, created_at=now - timedelta(hours=3)),
        _make_outcome(service="whatsapp", requested_code="213", assigned_code="469",
                      matched=False, created_at=now - timedelta(hours=4)),
    ]
    with _mock_session_local(rows):
        score = await PurchaseIntelligenceService.score_availability("whatsapp", "213")
    assert score.available is None   # 0.4 <= rate 0.5 < 0.6 → ambiguous
    assert score.success_rate == 0.5


@pytest.mark.asyncio
async def test_score_availability_recency_weight():
    """Older successes + a very recent failure → downgraded on recency penalty."""
    now = datetime.now(timezone.utc)
    rows = [
        # 2 old successes (weight 1 each)
        _make_outcome(service="whatsapp", assigned_code="213", requested_code="213",
                      matched=True, created_at=now - timedelta(days=1)),
        _make_outcome(service="whatsapp", assigned_code="213", requested_code="213",
                      matched=True, created_at=now - timedelta(days=1)),
        # 1 very recent failure (weight 3)
        _make_outcome(service="whatsapp", requested_code="213", assigned_code="469",
                      matched=False, created_at=now - timedelta(minutes=30)),
    ]
    with _mock_session_local(rows):
        score = await PurchaseIntelligenceService.score_availability("whatsapp", "213")
    # Total weighted: success=2, failure=3 → rate = 2/5 = 0.4
    assert score.success_rate == pytest.approx(0.4)


@pytest.mark.asyncio
async def test_unfiltered_purchase_scores_correctly():
    """Unfiltered buy (requested_code=None) that lands on 213 counts as a 213 success."""
    now = datetime.now(timezone.utc)
    rows = [
        _make_outcome(service="whatsapp", requested_code=None, assigned_code="213",
                      matched=None, created_at=now - timedelta(hours=1)),
    ]
    with _mock_session_local(rows):
        score = await PurchaseIntelligenceService.score_availability("whatsapp", "213")
    assert score.sample_size == 1
    assert score.success_rate == 1.0


@pytest.mark.asyncio
async def test_score_availability_db_error_gracefully_returns_unknown():
    """If the DB query raises, we get an unknown score instead of a 500."""
    mock_session = MagicMock()
    mock_session.query.side_effect = RuntimeError("DB exploded")
    with patch("app.services.purchase_intelligence.SessionLocal", return_value=mock_session):
        score = await PurchaseIntelligenceService.score_availability("whatsapp", "213")
    assert score.available is None
    assert score.confidence == 0.0
