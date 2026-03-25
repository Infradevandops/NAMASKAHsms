import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.models.user import User
from app.models.user_preference import UserPreference
from app.services.auto_topup_service import AutoTopupService


@pytest.fixture
def mock_paystack():
    with patch("app.services.auto_topup_service.PaystackService") as MockService:
        instance = MockService.return_value
        instance.charge_authorization = AsyncMock(return_value={"status": "success"})
        yield instance


@pytest.fixture
def auto_topup_service(db, mock_paystack):
    svc = AutoTopupService(db)
    svc.paystack = mock_paystack
    return svc


def _get_or_create_pref(db, user_id, **kwargs):
    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if not pref:
        pref = UserPreference(user_id=user_id, **kwargs)
        db.add(pref)
    else:
        for k, v in kwargs.items():
            setattr(pref, k, v)
    db.commit()
    return pref


def test_enable_auto_topup(auto_topup_service, db, regular_user):
    success = auto_topup_service.enable_auto_topup(regular_user.id, amount=50.0)
    assert success is True

    pref = db.query(UserPreference).filter(UserPreference.user_id == regular_user.id).first()
    assert pref.auto_recharge is True
    assert pref.recharge_amount == 50.0


def test_disable_auto_topup(auto_topup_service, db, regular_user):
    auto_topup_service.enable_auto_topup(regular_user.id)
    success = auto_topup_service.disable_auto_topup(regular_user.id)
    assert success is True

    pref = db.query(UserPreference).filter(UserPreference.user_id == regular_user.id).first()
    assert pref.auto_recharge is False


@pytest.mark.asyncio
async def test_check_and_topup_not_needed(auto_topup_service, db, regular_user):
    regular_user.credits = 100.0
    db.commit()
    _get_or_create_pref(db, regular_user.id, auto_recharge=True, auto_recharge_threshold=5.0)

    result = await auto_topup_service.check_and_topup(regular_user.id)
    assert result is None


@pytest.mark.asyncio
async def test_check_and_topup_disabled(auto_topup_service, db, regular_user):
    regular_user.credits = 1.0
    db.commit()
    _get_or_create_pref(db, regular_user.id, auto_recharge=False)

    result = await auto_topup_service.check_and_topup(regular_user.id)
    assert result is None


@pytest.mark.asyncio
async def test_check_and_topup_triggered(auto_topup_service, db, regular_user, mock_paystack):
    regular_user.credits = 1.0
    db.commit()
    _get_or_create_pref(
        db, regular_user.id,
        auto_recharge=True,
        auto_recharge_threshold=5.0,
        recharge_amount=20.0,
        paystack_authorization_code="auth_code_123",
    )

    with patch("app.services.auto_topup_service.PaymentLog") as MockLog:
        MockLog.return_value = MagicMock()
        with patch.object(auto_topup_service.db, "add"), \
             patch.object(auto_topup_service.db, "commit"):
            result = await auto_topup_service.check_and_topup(regular_user.id)

    assert result["status"] == "success"
    assert result["amount"] == 20.0
    mock_paystack.charge_authorization.assert_called_once()
