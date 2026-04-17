import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from app.services.purchase_intelligence import PurchaseIntelligenceService
from app.models.purchase_outcome import PurchaseOutcome

def _make_outcome(**kwargs):
    return PurchaseOutcome(**kwargs)

@pytest.fixture
def mock_db():
    return MagicMock()

def test_get_provider_roi_logic(mock_db):
    """Verifies ROI and Margin calculations are correct."""
    now = datetime.now(timezone.utc)
    outcomes = [
        # Provider A: 2 successful, 1 refunded
        _make_outcome(provider="provider_a", provider_cost=1.0, user_price=2.0, is_refunded=False, created_at=now),
        _make_outcome(provider="provider_a", provider_cost=1.0, user_price=2.0, is_refunded=False, created_at=now),
        _make_outcome(provider="provider_a", provider_cost=1.0, user_price=2.0, is_refunded=True, refund_amount=2.0, created_at=now),
    ]
    
    # Mock query.filter.all
    mock_db.query.return_value.filter.return_value.all.return_value = outcomes
    
    roi_data = PurchaseIntelligenceService.get_provider_roi(mock_db, days=7)
    
    assert "provider_a" in roi_data
    stats = roi_data["provider_a"]
    
    # Total Rev = 2+2+2 = 6.0
    # Total Cost = 1+1+1 = 3.0
    # Total Refund = 2.0
    # Gross Profit = 6 - 3 = 3.0
    # Net Profit = 3 - 2 = 1.0
    # ROI % = (Gross / Cost) * 100 = (3/3) * 100 = 100%
    
    assert stats["roi_pct"] == 100.0
    assert stats["net_profit"] == 1.0
    # Efficiency = 100 * (1 - (2/6)) = 100 * (4/6) = 66.67
    assert stats["efficiency_score"] == pytest.approx(66.67, 0.01)

def test_get_carrier_sentiment_aggregation(mock_db):
    """Verifies carrier success rate aggregation logic."""
    # Mock row objects (namedtuples since SQLAlchemy .all() on columns returns them)
    from collections import namedtuple
    Row = namedtuple("Row", ["assigned_carrier", "total", "successes"])
    
    results = [
        Row("att", 10, 9),      # 90%
        Row("tmobile", 10, 5),  # 50%
        Row("verizon", 5, 5),   # 100%
    ]
    
    mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = results
    
    sentiment = PurchaseIntelligenceService.get_carrier_sentiment(mock_db, "whatsapp")
    
    assert sentiment["att"] == 0.9
    assert sentiment["tmobile"] == 0.5
    assert sentiment["verizon"] == 1.0
