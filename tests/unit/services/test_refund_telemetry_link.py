from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.purchase_outcome import PurchaseOutcome
from app.services.refund_service import RefundService


@pytest.mark.asyncio
async def test_refund_updates_purchase_outcome_telemetry():
    """Verifies that RefundService links the refund to the telemetry record."""
    # Mocking
    mock_db = MagicMock()
    mock_verification = MagicMock()
    mock_verification.id = "test-verification-id"

    mock_user = MagicMock()
    mock_user.id = "test-user-id"
    mock_user.credits = 10.0
    mock_user.subscription_tier = "payg"

    # We want to test the _create_refund_transaction part
    service = RefundService()

    with patch("sqlalchemy.update") as mock_update:
        await service._create_refund_transaction(
            db=mock_db,
            user=mock_user,
            verification=mock_verification,
            amount=0.55,
            refund_type="surcharge",
            reasons=["area_code_mismatch"],
        )

        # Check if update was called on PurchaseOutcome
        mock_update.assert_called_once_with(PurchaseOutcome)

        # Check if where clause and values were set
        mock_stmt = mock_update.return_value
        mock_stmt.where.assert_called_once()
        mock_stmt.where.return_value.values.assert_called_once_with(
            is_refunded=True, refund_amount=0.55
        )

        # Check if executed
        mock_db.execute.assert_called_once()
