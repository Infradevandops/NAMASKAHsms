"""Enhanced tests for payment service."""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from app.services.payment_service import PaymentService
from app.models.payment import Payment, Transaction
from app.core.exceptions import InsufficientCreditsError, PaymentError


@pytest.fixture
def payment_service():
    """Create payment service instance."""
    db_mock = Mock(spec=Session)
    return PaymentService(db_mock)


@pytest.fixture
def mock_user():
    """Create mock user."""
    user = Mock()
    user.id = "user123"
    user.email = "test@example.com"
    user.credits = Decimal("100.00")
    return user


@pytest.fixture
def mock_payment():
    """Create mock payment."""
    payment = Mock(spec=Payment)
    payment.id = "payment123"
    payment.user_id = "user123"
    payment.amount = Decimal("50.00")
    payment.status = "completed"
    payment.created_at = datetime.utcnow()
    return payment


class TestPaymentService:
    """Test cases for payment service."""

    def test_add_credits_success(self, payment_service, mock_user):
        """Test successful credit addition."""
        initial_credits = mock_user.credits
        amount = Decimal("50.00")

        result = payment_service.add_credits(mock_user, amount)

        assert result is not None
        assert result.amount == amount
        assert result.status == "completed"

    def test_add_credits_invalid_amount(self, payment_service, mock_user):
        """Test credit addition with invalid amount."""
        with pytest.raises(ValueError):
            payment_service.add_credits(mock_user, Decimal("-10.00"))

        with pytest.raises(ValueError):
            payment_service.add_credits(mock_user, Decimal("0.00"))

    def test_add_credits_max_exceeded(self, payment_service, mock_user):
        """Test credit addition exceeding maximum."""
        mock_user.credits = Decimal("999999.00")

        with pytest.raises(ValueError):
            payment_service.add_credits(mock_user, Decimal("1.00"))

    def test_deduct_credits_success(self, payment_service, mock_user):
        """Test successful credit deduction."""
        initial_credits = mock_user.credits
        amount = Decimal("10.00")

        result = payment_service.deduct_credits(mock_user, amount, "verification")

        assert result is True
        assert mock_user.credits == initial_credits - amount

    def test_deduct_credits_insufficient(self, payment_service, mock_user):
        """Test credit deduction with insufficient credits."""
        mock_user.credits = Decimal("5.00")

        with pytest.raises(InsufficientCreditsError):
            payment_service.deduct_credits(mock_user, Decimal("10.00"), "verification")

    def test_deduct_credits_zero_amount(self, payment_service, mock_user):
        """Test credit deduction with zero amount."""
        with pytest.raises(ValueError):
            payment_service.deduct_credits(mock_user, Decimal("0.00"), "verification")

    def test_process_payment_success(self, payment_service, mock_user):
        """Test successful payment processing."""
        payment_data = {
            "amount": Decimal("50.00"),
            "method": "credit_card",
            "currency": "USD"
        }

        result = payment_service.process_payment(mock_user, payment_data)

        assert result is not None
        assert result.status == "completed"
        assert result.amount == Decimal("50.00")

    def test_process_payment_invalid_method(self, payment_service, mock_user):
        """Test payment processing with invalid method."""
        payment_data = {
            "amount": Decimal("50.00"),
            "method": "invalid_method",
            "currency": "USD"
        }

        with pytest.raises(PaymentError):
            payment_service.process_payment(mock_user, payment_data)

    def test_process_payment_invalid_currency(self, payment_service, mock_user):
        """Test payment processing with invalid currency."""
        payment_data = {
            "amount": Decimal("50.00"),
            "method": "credit_card",
            "currency": "INVALID"
        }

        with pytest.raises(PaymentError):
            payment_service.process_payment(mock_user, payment_data)

    def test_refund_success(self, payment_service, mock_payment):
        """Test successful refund."""
        result = payment_service.refund(mock_payment)

        assert result is not None
        assert result.status == "refunded"

    def test_refund_already_refunded(self, payment_service, mock_payment):
        """Test refund of already refunded payment."""
        mock_payment.status = "refunded"

        with pytest.raises(PaymentError):
            payment_service.refund(mock_payment)

    def test_refund_not_found(self, payment_service):
        """Test refund of non-existent payment."""
        with pytest.raises(PaymentError):
            payment_service.refund(None)

    def test_get_transaction_history(self, payment_service, mock_user):
        """Test getting transaction history."""
        transactions = [
            Mock(id="trans1", amount=Decimal("10.00"), created_at=datetime.utcnow()),
            Mock(id="trans2", amount=Decimal("20.00"), created_at=datetime.utcnow()),
        ]

        with patch.object(payment_service.db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.order_by.return_value.all.return_value = transactions

            result = payment_service.get_transaction_history(mock_user)

            assert len(result) == 2
            assert result[0].amount == Decimal("10.00")

    def test_get_transaction_history_pagination(self, payment_service, mock_user):
        """Test transaction history with pagination."""
        transactions = [Mock(id=f"trans{i}", amount=Decimal("10.00")) for i in range(50)]

        with patch.object(payment_service.db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.order_by.return_value.limit.return_value.offset.return_value.all.return_value = transactions[:10]

            result = payment_service.get_transaction_history(mock_user, page=1, limit=10)

            assert len(result) == 10

    def test_get_balance(self, payment_service, mock_user):
        """Test getting user balance."""
        result = payment_service.get_balance(mock_user)

        assert result == mock_user.credits

    def test_validate_payment_amount(self, payment_service):
        """Test payment amount validation."""
        # Valid amounts
        assert payment_service.validate_payment_amount(Decimal("0.01")) is True
        assert payment_service.validate_payment_amount(Decimal("100.00")) is True
        assert payment_service.validate_payment_amount(Decimal("10000.00")) is True

        # Invalid amounts
        assert payment_service.validate_payment_amount(Decimal("0.00")) is False
        assert payment_service.validate_payment_amount(Decimal("-10.00")) is False
        assert payment_service.validate_payment_amount(Decimal("100000.00")) is False

    def test_calculate_fee(self, payment_service):
        """Test fee calculation."""
        amount = Decimal("100.00")
        fee = payment_service.calculate_fee(amount)

        assert fee > Decimal("0.00")
        assert fee < amount

    def test_apply_discount(self, payment_service, mock_user):
        """Test discount application."""
        amount = Decimal("100.00")
        discount_code = "SAVE10"

        with patch.object(payment_service, 'validate_discount_code', return_value=True):
            with patch.object(payment_service, 'get_discount_percentage', return_value=10):
                result = payment_service.apply_discount(amount, discount_code)

                assert result == Decimal("90.00")

    def test_apply_invalid_discount(self, payment_service):
        """Test invalid discount application."""
        amount = Decimal("100.00")
        discount_code = "INVALID"

        with patch.object(payment_service, 'validate_discount_code', return_value=False):
            with pytest.raises(PaymentError):
                payment_service.apply_discount(amount, discount_code)

    def test_get_payment_methods(self, payment_service):
        """Test getting available payment methods."""
        methods = payment_service.get_payment_methods()

        assert len(methods) > 0
        assert "credit_card" in methods
        assert "paypal" in methods or "bank_transfer" in methods

    def test_validate_payment_method(self, payment_service):
        """Test payment method validation."""
        assert payment_service.validate_payment_method("credit_card") is True
        assert payment_service.validate_payment_method("paypal") is True
        assert payment_service.validate_payment_method("invalid") is False

    def test_get_supported_currencies(self, payment_service):
        """Test getting supported currencies."""
        currencies = payment_service.get_supported_currencies()

        assert len(currencies) > 0
        assert "USD" in currencies
        assert "EUR" in currencies or "GBP" in currencies

    def test_validate_currency(self, payment_service):
        """Test currency validation."""
        assert payment_service.validate_currency("USD") is True
        assert payment_service.validate_currency("EUR") is True
        assert payment_service.validate_currency("INVALID") is False

    def test_convert_currency(self, payment_service):
        """Test currency conversion."""
        amount = Decimal("100.00")

        with patch.object(payment_service, 'get_exchange_rate', return_value=Decimal("0.85")):
            result = payment_service.convert_currency(amount, "USD", "EUR")

            assert result == Decimal("85.00")

    def test_get_payment_status(self, payment_service, mock_payment):
        """Test getting payment status."""
        status = payment_service.get_payment_status(mock_payment)

        assert status == "completed"

    def test_cancel_payment(self, payment_service, mock_payment):
        """Test payment cancellation."""
        mock_payment.status = "pending"

        result = payment_service.cancel_payment(mock_payment)

        assert result is not None
        assert result.status == "cancelled"

    def test_cancel_completed_payment(self, payment_service, mock_payment):
        """Test cancellation of completed payment."""
        mock_payment.status = "completed"

        with pytest.raises(PaymentError):
            payment_service.cancel_payment(mock_payment)

    def test_retry_failed_payment(self, payment_service, mock_payment):
        """Test retrying failed payment."""
        mock_payment.status = "failed"

        result = payment_service.retry_payment(mock_payment)

        assert result is not None
        assert result.status in ["completed", "pending"]

    def test_get_payment_receipt(self, payment_service, mock_payment):
        """Test getting payment receipt."""
        receipt = payment_service.get_payment_receipt(mock_payment)

        assert receipt is not None
        assert "payment_id" in receipt
        assert "amount" in receipt
        assert "date" in receipt

    def test_export_transaction_history(self, payment_service, mock_user):
        """Test exporting transaction history."""
        with patch.object(payment_service, 'get_transaction_history', return_value=[]):
            result = payment_service.export_transaction_history(mock_user, format="csv")

            assert result is not None
            assert isinstance(result, str)

    def test_get_payment_analytics(self, payment_service, mock_user):
        """Test getting payment analytics."""
        analytics = payment_service.get_payment_analytics(mock_user)

        assert analytics is not None
        assert "total_spent" in analytics
        assert "total_refunded" in analytics
        assert "average_transaction" in analytics
