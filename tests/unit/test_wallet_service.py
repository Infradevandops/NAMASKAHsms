"""Unit tests for wallet service business logic."""


import pytest
from app.models.transaction import Transaction
from app.models.user import User
from app.services.credit_service import CreditService
from app.services.pricing_calculator import PricingCalculator
from app.core.exceptions import InsufficientCreditsError
from app.core.exceptions import InsufficientCreditsError

class TestWalletSMSCostCalculations:

    """Test SMS cost calculation logic using PricingCalculator."""

    def test_calculate_sms_cost_payg_base(self, db_session):

        """Base SMS cost for PAYG: $2.50."""
        user = User(email="payg@example.com", subscription_tier="payg", credits=10.0)
        db_session.add(user)
        db_session.commit()

        result = PricingCalculator.calculate_sms_cost(db_session, user.id, {})
        assert result["base_cost"] == 2.50
        assert result["filter_charges"] == 0.0
        assert result["total_cost"] == 2.50

    def test_calculate_sms_cost_payg_location_filter(self, db_session):

        """Location filter: +$0.25 for PAYG."""
        user = User(email="payg_loc@example.com", subscription_tier="payg", credits=10.0)
        db_session.add(user)
        db_session.commit()

        # filter keys: state/city trigger +0.25
        result = PricingCalculator.calculate_sms_cost(db_session, user.id, {"state": "CA"})
        assert result["filter_charges"] == 0.25
        assert result["total_cost"] == 2.50 + 0.25

    def test_calculate_sms_cost_payg_isp_filter(self, db_session):

        """ISP filter: +$0.50 for PAYG."""
        user = User(email="payg_isp@example.com", subscription_tier="payg", credits=10.0)
        db_session.add(user)
        db_session.commit()

        result = PricingCalculator.calculate_sms_cost(db_session, user.id, {"isp": "T-Mobile"})
        assert result["filter_charges"] == 0.50
        assert result["total_cost"] == 2.50 + 0.50

    def test_calculate_sms_cost_payg_all_filters(self, db_session):

        """All filters: +$0.75 for PAYG."""
        user = User(email="payg_all@example.com", subscription_tier="payg", credits=10.0)
        db_session.add(user)
        db_session.commit()

        result = PricingCalculator.calculate_sms_cost(db_session, user.id, {"state": "CA", "isp": "Verizon"})
        assert result["filter_charges"] == 0.75
        assert result["total_cost"] == 2.50 + 0.75

    def test_calculate_sms_cost_pro_tier_filters_included(self, db_session):

        """Pro tier: Filters included (no extra charge)."""
        user = User(email="pro@example.com", subscription_tier="pro", credits=50.0)
        db_session.add(user)
        db_session.commit()

        result = PricingCalculator.calculate_sms_cost(db_session, user.id, {"state": "CA", "isp": "Verizon"})
        assert result["filter_charges"] == 0.0
        assert result["total_cost"] == 2.50  # Base cost only


class TestWalletTransactions:

        """Test transaction recording via CreditService."""

    def test_add_credits_transaction(self, db_session):

        """Test adding credits records a transaction."""
        user = User(email="test_add@example.com", subscription_tier="freemium", credits=0)
        db_session.add(user)
        db_session.commit()

        credit_service = CreditService(db_session)
        credit_service.add_credits(
            user_id=user.id,
            amount=20.0,
            description="Paystack deposit",
            transaction_type="credit",
        )

        tx = db_session.query(Transaction).filter(Transaction.user_id == user.id).first()
        assert tx is not None
        assert tx.type == "credit"
        assert tx.amount == 20.0
        assert tx.description == "Paystack deposit"

    def test_deduct_credits_transaction(self, db_session):

        """Test deducting credits records a transaction."""
        user = User(email="test_deduct@example.com", subscription_tier="freemium", credits=10.0)
        db_session.add(user)
        db_session.commit()

        credit_service = CreditService(db_session)
        credit_service.deduct_credits(
            user_id=user.id,
            amount=2.50,
            description="SMS verification",
            transaction_type="debit",
        )

        tx = db_session.query(Transaction).filter(Transaction.user_id == user.id).first()
        assert tx is not None
        assert tx.type == "debit"
        assert tx.amount == -2.50

    def test_transaction_history_pagination(self, db_session):

        """Test transaction history pagination."""
        user = User(email="test_page@example.com", subscription_tier="freemium", credits=100.0)
        db_session.add(user)
        db_session.commit()

        # Create 25 transactions
        for i in range(25):
            tx = Transaction(user_id=user.id, type="credit", amount=10.0, description=f"Deposit {i}")
            db_session.add(tx)
        db_session.commit()

        credit_service = CreditService(db_session)

        # Get first page (limit 15)
        result1 = credit_service.get_transaction_history(user.id, limit=15)
        assert len(result1["transactions"]) == 15
        assert result1["total"] == 25

        # Get second page (skip 15, limit 15)
        result2 = credit_service.get_transaction_history(user.id, skip=15, limit=15)
        assert len(result2["transactions"]) == 10
        assert result2["total"] == 25


class TestWalletBalanceOperations:

        """Test wallet balance operations via CreditService."""

    def test_deduct_credits_sufficient_balance(self, db_session):

        """User has $10, deduct $5."""
        user = User(email="balance_ok@example.com", subscription_tier="freemium", credits=10.0)
        db_session.add(user)
        db_session.commit()

        credit_service = CreditService(db_session)
        credit_service.deduct_credits(user.id, 5.0)

        db_session.refresh(user)
        assert user.credits == 5.0

    def test_deduct_credits_insufficient_balance(self, db_session):

        """User has $3, try to deduct $5."""
        user = User(email="balance_low@example.com", subscription_tier="freemium", credits=3.0)
        db_session.add(user)
        db_session.commit()

        credit_service = CreditService(db_session)


        with pytest.raises(InsufficientCreditsError):
            credit_service.deduct_credits(user.id, 5.0)

    def test_validate_balance_freemium_bonus(self, db_session):

        """Test validate_balance for freemium with bonus SMS."""
        user = User(
            email="free_bonus@example.com",
            subscription_tier="freemium",
            credits=0,
            bonus_sms_balance=2,  # Has free SMS
        )
        db_session.add(user)
        db_session.commit()

        # Should pass validation for any cost since bonus > 0 logic exists in PricingCalculator.validate_balance
        # Note: PricingCalculator.validate_balance checks bonus_sms_balance >= 1 for freemium
        is_valid = PricingCalculator.validate_balance(db_session, user.id, 5.0)
        assert is_valid is True


class TestCreditServiceTransfer:

        """Test credit transfer functionality."""

    def test_transfer_credits_success(self, db_session):

        """Test successful transfer between users."""
        sender = User(email="sender@example.com", subscription_tier="pro", credits=100.0)
        recipient = User(email="recipient@example.com", subscription_tier="freemium", credits=0.0)
        db_session.add(sender)
        db_session.add(recipient)
        db_session.commit()

        credit_service = CreditService(db_session)
        result = credit_service.transfer_credits(sender.id, recipient.id, 50.0, "Gift")

        db_session.refresh(sender)
        db_session.refresh(recipient)

        assert sender.credits == 50.0
        assert recipient.credits == 50.0
        assert result["amount"] == 50.0

        # Verify transactions
        txs_sender = (
            db_session.query(Transaction).filter(Transaction.user_id == sender.id, Transaction.type == "transfer").all()
        )
        txs_recipient = (
            db_session.query(Transaction)
            .filter(Transaction.user_id == recipient.id, Transaction.type == "transfer")
            .all()
        )
        assert len(txs_sender) == 1
        assert len(txs_recipient) == 1
        assert txs_sender[0].amount == -50.0
        assert txs_recipient[0].amount == 50.0

    def test_transfer_credits_insufficient_funds(self, db_session):

        """Test transfer fails with insufficient funds."""
        sender = User(email="poor_sender@example.com", subscription_tier="freemium", credits=10.0)
        recipient = User(email="rich_recipient@example.com", subscription_tier="pro", credits=100.0)
        db_session.add(sender)
        db_session.add(recipient)
        db_session.commit()

        credit_service = CreditService(db_session)

        with pytest.raises(InsufficientCreditsError):
            credit_service.transfer_credits(sender.id, recipient.id, 50.0)

    def test_transfer_credits_self_transfer(self, db_session):
        # Logic doesn't explicitly forbid self-transfer in service but it's a good edge case.
        # Assuming logic allows it or behaves neutrally.
        pass


class TestCreditServiceAdmin:

        """Test admin credit operations."""

    def test_reset_credits(self, db_session):

        """Test admin reset credits."""
        user = User(email="reset_target@example.com", subscription_tier="freemium", credits=50.0)
        db_session.add(user)
        db_session.commit()

        credit_service = CreditService(db_session)
        result = credit_service.reset_credits(user.id, 100.0)

        db_session.refresh(user)
        assert user.credits == 100.0
        assert result["old_balance"] == 50.0
        assert result["new_balance"] == 100.0

        tx = (
            db_session.query(Transaction)
            .filter(Transaction.user_id == user.id, Transaction.type == "admin_reset")
            .first()
        )
        assert tx is not None
        assert tx.amount == 50.0  # 100 - 50

    def test_get_transaction_summary(self, db_session):

        """Test transaction summary generation."""
        user = User(email="summary_user@example.com", subscription_tier="freemium", credits=0.0)
        db_session.add(user)
        db_session.commit()

        credit_service = CreditService(db_session)
        credit_service.add_credits(user.id, 100.0, transaction_type="credit")
        credit_service.deduct_credits(user.id, 20.0, transaction_type="debit")
        credit_service.add_credits(user.id, 5.0, transaction_type="bonus")

        summary = credit_service.get_transaction_summary(user.id)

        assert summary["total_credits_added"] == 100.0
        assert summary["total_credits_deducted"] == 20.0
        assert summary["total_bonuses"] == 5.0
        assert summary["current_balance"] == 85.0
