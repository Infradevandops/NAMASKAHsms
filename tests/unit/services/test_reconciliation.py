import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone
from app.api.admin.area_code_analytics import get_provider_analytics
from app.models.purchase_outcome import PurchaseOutcome


@pytest.mark.asyncio
async def test_provider_analytics_calculates_leakage():
    """Verifies that the provider analytics correctly calculates margin leakage and outcome distribution."""
    mock_db = MagicMock()

    # Create test outcomes
    # 1. Success
    o1 = PurchaseOutcome(
        provider="test_prov",
        sms_received=True,
        provider_cost=0.50,
        user_price=1.00,
        is_refunded=False,
        outcome_category="SUCCESS",
        created_at=datetime.now(timezone.utc),
    )
    # 2. Refunded and RECOUPED (No Leakage)
    o2 = PurchaseOutcome(
        provider="test_prov",
        sms_received=False,
        provider_cost=0.50,
        user_price=1.00,
        is_refunded=True,
        refund_amount=1.00,
        provider_refunded=True,  # Successfully recouped
        outcome_category="NETWORK",
        created_at=datetime.now(timezone.utc),
    )
    # 3. Refunded but NOT Recouped (LEAKAGE!)
    o3 = PurchaseOutcome(
        provider="test_prov",
        sms_received=False,
        provider_cost=0.40,
        user_price=1.00,
        is_refunded=True,
        refund_amount=1.00,
        provider_refunded=False,  # LEAKAGE
        outcome_category="NETWORK",
        created_at=datetime.now(timezone.utc),
    )
    # 4. Product Mismatch (Auto Recouped)
    o4 = PurchaseOutcome(
        provider="test_prov",
        sms_received=False,
        provider_cost=0.50,
        user_price=1.00,
        is_refunded=True,
        refund_amount=1.00,
        provider_refunded=True,
        outcome_category="PRODUCT",
        created_at=datetime.now(timezone.utc),
    )

    mock_db.query.return_value.filter.return_value.all.return_value = [o1, o2, o3, o4]

    result = await get_provider_analytics(days=7, db=mock_db, user_id="admin")

    perf = result["provider_performance"][0]
    financials = perf["financials"]

    # Leakage should be 0.40 (from o3)
    assert financials["margin_leakage"] == 0.40

    # Recoup rate should be 2/3 = 0.67
    assert financials["recoup_rate"] == 0.67

    # Outcome distribution check
    dist = perf["outcome_distribution"]
    assert dist["NETWORK"] == 2
    assert dist["PRODUCT"] == 1
    assert dist["SUCCESS"] == 1
