

import pytest
from app.core.exceptions import InsufficientCreditsError
from app.services.credit_service import CreditService

class TestCreditService:
    @pytest.fixture
    def service(self, db_session):

        return CreditService(db_session)

    def test_get_balance(self, service, regular_user):

        balance = service.get_balance(regular_user.id)
        assert balance == 10.0

    def test_add_credits(self, service, regular_user, db_session):

        res = service.add_credits(regular_user.id, 5.0, "Bonus")
        assert res["new_balance"] == 15.0
        db_session.refresh(regular_user)
        assert regular_user.credits == 15.0

    def test_deduct_credits(self, service, regular_user, db_session):

        res = service.deduct_credits(regular_user.id, 5.0, "Purchase")
        assert res["new_balance"] == 5.0
        db_session.refresh(regular_user)
        assert regular_user.credits == 5.0

    def test_deduct_insufficient_credits(self, service, regular_user):

        with pytest.raises(InsufficientCreditsError):
            service.deduct_credits(regular_user.id, 20.0, "Overdrawn")