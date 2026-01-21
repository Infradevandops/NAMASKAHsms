import pytest

from app.core.exceptions import InsufficientCreditsError
from app.models.transaction import Transaction
from app.services.credit_service import CreditService


class TestCreditServiceComplete:
    """Comprehensive tests for CreditService."""

    def test_get_balance(self, db_session, regular_user):
        """Test getting user balance."""
        service = CreditService(db_session)
        balance = service.get_balance(regular_user.id)
        assert balance == regular_user.credits

    def test_add_credits(self, db_session, regular_user):
        """Test adding credits."""
        service = CreditService(db_session)
        initial_balance = regular_user.credits
        amount = 50.0

        result = service.add_credits(regular_user.id, amount, "Test credit")

        assert result["new_balance"] == initial_balance + amount
        assert (
            db_session.query(Transaction)
            .filter(Transaction.user_id == regular_user.id)
            .count()
            == 1
        )

    def test_deduct_credits_success(self, db_session, regular_user):
        """Test successful credit deduction."""
        service = CreditService(db_session)
        # Give some credits first
        service.add_credits(regular_user.id, 100.0)

        initial_balance = regular_user.credits
        amount = 30.0

        result = service.deduct_credits(regular_user.id, amount, "Test deduction")

        assert result["new_balance"] == initial_balance - amount

    def test_deduct_credits_insufficient(self, db_session, regular_user):
        """Test deduction fails with insufficient credits."""
        service = CreditService(db_session)
        # Set balance to 10
        regular_user.credits = 10.0
        db_session.commit()

        with pytest.raises(InsufficientCreditsError):
            service.deduct_credits(regular_user.id, 20.0)

    def test_transfer_credits(self, db_session, regular_user, admin_user):
        """Test transferring credits between users."""
        service = CreditService(db_session)

        # Give regular user 100 credits
        service.add_credits(regular_user.id, 100.0)

        initial_reg_balance = regular_user.credits
        initial_admin_balance = admin_user.credits
        amount = 40.0

        result = service.transfer_credits(regular_user.id, admin_user.id, amount)

        assert result["from_user_new_balance"] == initial_reg_balance - amount
        assert result["to_user_new_balance"] == initial_admin_balance + amount

        # Check transaction records (one for each user)
        reg_trans = (
            db_session.query(Transaction)
            .filter(
                Transaction.user_id == regular_user.id, Transaction.type == "transfer"
            )
            .first()
        )
        admin_trans = (
            db_session.query(Transaction)
            .filter(
                Transaction.user_id == admin_user.id, Transaction.type == "transfer"
            )
            .first()
        )

        assert reg_trans.amount == -amount
        assert admin_trans.amount == amount

    def test_get_transaction_history(self, db_session, regular_user):
        """Test retrieving transaction history."""
        service = CreditService(db_session)

        service.add_credits(regular_user.id, 10.0, "C1")
        service.add_credits(regular_user.id, 20.0, "C2")
        service.deduct_credits(regular_user.id, 5.0, "D1")

        history = service.get_transaction_history(regular_user.id)
        assert history["total"] == 3
        assert len(history["transactions"]) == 3
