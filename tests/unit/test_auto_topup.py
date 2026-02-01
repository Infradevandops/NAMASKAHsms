

from unittest.mock import AsyncMock, patch
import pytest
from app.models.user import User
from app.services.auto_topup_service import AutoTopupService

@pytest.fixture
def mock_payment_service():

with patch("app.services.auto_topup_service.PaymentService") as MockService:
        service_instance = MockService.return_value
        service_instance.initialize_payment = AsyncMock()
        yield service_instance


@pytest.fixture
def auto_topup_service(db, mock_payment_service):

    return AutoTopupService(db)


def test_enable_auto_topup(auto_topup_service, db, regular_user):

    success = auto_topup_service.enable_auto_topup(regular_user.id, amount=50.0)
    assert success is True

    # Refresh user
    user = db.query(User).filter(User.id == regular_user.id).first()
    assert user.auto_topup_enabled is True
    assert user.auto_topup_amount == 50.0


def test_disable_auto_topup(auto_topup_service, db, regular_user):

    auto_topup_service.enable_auto_topup(regular_user.id)
    success = auto_topup_service.disable_auto_topup(regular_user.id)
    assert success is True

    user = db.query(User).filter(User.id == regular_user.id).first()
    assert user.auto_topup_enabled is False


@pytest.mark.asyncio
async def test_check_and_topup_not_needed(auto_topup_service, db, regular_user):
    # Set high balance
    regular_user.credits = 100.0
    regular_user.auto_topup_enabled = True
    db.commit()

    result = await auto_topup_service.check_and_topup(regular_user.id)
    assert result is None


@pytest.mark.asyncio
async def test_check_and_topup_disabled(auto_topup_service, db, regular_user):
    # Set low balance but disabled
    regular_user.credits = 1.0
    regular_user.auto_topup_enabled = False
    db.commit()

    result = await auto_topup_service.check_and_topup(regular_user.id)
    assert result is None


@pytest.mark.asyncio
async def test_check_and_topup_triggered(auto_topup_service, db, regular_user, mock_payment_service):
    # Set low balance and enabled
    regular_user.credits = 1.0
    regular_user.auto_topup_enabled = True
    db.commit()

    # Mock payment response
    mock_payment_service.initialize_payment.return_value = {
        "authorization_url": "http://pay.com",
        "reference": "ref123",
    }

    result = await auto_topup_service.check_and_topup(regular_user.id)

    assert result["status"] == "initiated"
    assert result["payment_url"] == "http://pay.com"
    mock_payment_service.initialize_payment.assert_called_once()
