"""Enhanced tests for rental service."""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from app.services.rental_service import RentalService
from app.models.rental import Rental
from app.core.exceptions import InsufficientCreditsError, RentalError


@pytest.fixture
def rental_service():
    """Create rental service instance."""
    db_mock = Mock(spec=Session)
    return RentalService(db_mock)


@pytest.fixture
def mock_user():
    """Create mock user."""
    user = Mock()
    user.id = "user123"
    user.email = "test@example.com"
    user.credits = Decimal("100.00")
    return user


@pytest.fixture
def mock_rental():
    """Create mock rental."""
    rental = Mock(spec=Rental)
    rental.id = "rental123"
    rental.user_id = "user123"
    rental.phone_number = "+1234567890"
    rental.service_name = "whatsapp"
    rental.country_code = "us"
    rental.expires_at = datetime.utcnow() + timedelta(hours=24)
    rental.cost = Decimal("0.50")
    rental.is_expired = False
    rental.time_remaining_seconds = 86400
    rental.activation_id = "activation123"
    return rental


class TestRentalServiceEnhanced:
    """Enhanced test cases for rental service."""

    def test_create_rental_success(self, rental_service, mock_user):
        """Test successful rental creation."""
        rental_data = {
            "service_name": "whatsapp",
            "country_code": "us",
            "duration_hours": 24
        }

        with patch.object(rental_service, '_get_user', return_value=mock_user):
            with patch.object(rental_service, '_buy_number', return_value="+1234567890"):
                result = rental_service.create_rental(mock_user, rental_data)

                assert result is not None
                assert result.phone_number == "+1234567890"
                assert result.service_name == "whatsapp"

    def test_create_rental_insufficient_credits(self, rental_service, mock_user):
        """Test rental creation with insufficient credits."""
        mock_user.credits = Decimal("0.10")
        rental_data = {
            "service_name": "whatsapp",
            "country_code": "us",
            "duration_hours": 24
        }

        with pytest.raises(InsufficientCreditsError):
            rental_service.create_rental(mock_user, rental_data)

    def test_create_rental_invalid_duration(self, rental_service, mock_user):
        """Test rental creation with invalid duration."""
        rental_data = {
            "service_name": "whatsapp",
            "country_code": "us",
            "duration_hours": 0
        }

        with pytest.raises(ValueError):
            rental_service.create_rental(mock_user, rental_data)

    def test_create_rental_invalid_service(self, rental_service, mock_user):
        """Test rental creation with invalid service."""
        rental_data = {
            "service_name": "invalid_service",
            "country_code": "us",
            "duration_hours": 24
        }

        with pytest.raises(ValueError):
            rental_service.create_rental(mock_user, rental_data)

    def test_create_rental_invalid_country(self, rental_service, mock_user):
        """Test rental creation with invalid country."""
        rental_data = {
            "service_name": "whatsapp",
            "country_code": "invalid",
            "duration_hours": 24
        }

        with pytest.raises(ValueError):
            rental_service.create_rental(mock_user, rental_data)

    def test_get_active_rentals(self, rental_service, mock_user):
        """Test getting active rentals."""
        rentals = [mock_rental for _ in range(3)]

        with patch.object(rental_service.db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.all.return_value = rentals

            result = rental_service.get_active_rentals(mock_user)

            assert len(result) == 3

    def test_get_active_rentals_empty(self, rental_service, mock_user):
        """Test getting active rentals when none exist."""
        with patch.object(rental_service.db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.all.return_value = []

            result = rental_service.get_active_rentals(mock_user)

            assert len(result) == 0

    def test_get_rental_status(self, rental_service, mock_rental):
        """Test getting rental status."""
        status = rental_service.get_rental_status(mock_rental)

        assert status is not None
        assert "phone_number" in status
        assert "service_name" in status
        assert "expires_at" in status
        assert "time_remaining" in status

    def test_get_rental_status_expired(self, rental_service, mock_rental):
        """Test getting status of expired rental."""
        mock_rental.is_expired = True
        mock_rental.expires_at = datetime.utcnow() - timedelta(hours=1)

        status = rental_service.get_rental_status(mock_rental)

        assert status["is_expired"] is True
        assert status["time_remaining"] <= 0

    def test_extend_rental_success(self, rental_service, mock_user, mock_rental):
        """Test successful rental extension."""
        extend_data = {"additional_hours": 12}

        with patch.object(rental_service, '_get_rental', return_value=mock_rental):
            with patch.object(rental_service, '_get_user', return_value=mock_user):
                result = rental_service.extend_rental(mock_rental, mock_user, extend_data)

                assert result is not None
                assert "extension_cost" in result

    def test_extend_rental_insufficient_credits(self, rental_service, mock_user, mock_rental):
        """Test rental extension with insufficient credits."""
        mock_user.credits = Decimal("0.10")
        extend_data = {"additional_hours": 24}

        with patch.object(rental_service, '_get_rental', return_value=mock_rental):
            with pytest.raises(InsufficientCreditsError):
                rental_service.extend_rental(mock_rental, mock_user, extend_data)

    def test_extend_rental_expired(self, rental_service, mock_user, mock_rental):
        """Test extending expired rental."""
        mock_rental.is_expired = True

        with patch.object(rental_service, '_get_rental', return_value=mock_rental):
            with pytest.raises(RentalError):
                rental_service.extend_rental(mock_rental, mock_user, {"additional_hours": 12})

    def test_extend_rental_invalid_duration(self, rental_service, mock_user, mock_rental):
        """Test rental extension with invalid duration."""
        extend_data = {"additional_hours": 0}

        with pytest.raises(ValueError):
            rental_service.extend_rental(mock_rental, mock_user, extend_data)

    def test_check_expired_rentals(self, rental_service):
        """Test checking for expired rentals."""
        expired_rentals = [mock_rental for _ in range(2)]

        with patch.object(rental_service.db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.all.return_value = expired_rentals

            result = rental_service.check_expired_rentals()

            assert len(result) == 2

    def test_expire_rental_success(self, rental_service, mock_rental):
        """Test successful rental expiration."""
        mock_rental.is_expired = False

        result = rental_service.expire_rental(mock_rental)

        assert result is not None
        assert result.is_expired is True

    def test_get_rental_messages(self, rental_service, mock_rental):
        """Test getting rental messages."""
        messages = [
            {"text": "Your code is 123456", "timestamp": datetime.utcnow()},
            {"text": "Your code is 789012", "timestamp": datetime.utcnow()}
        ]

        with patch.object(rental_service, '_fetch_messages', return_value=messages):
            result = rental_service.get_rental_messages(mock_rental)

            assert len(result) == 2
            assert "123456" in result[0]["text"]

    def test_get_rental_messages_empty(self, rental_service, mock_rental):
        """Test getting rental messages when none exist."""
        with patch.object(rental_service, '_fetch_messages', return_value=[]):
            result = rental_service.get_rental_messages(mock_rental)

            assert len(result) == 0

    def test_release_rental_success(self, rental_service, mock_rental):
        """Test successful rental release."""
        result = rental_service.release_rental(mock_rental)

        assert result is not None
        assert result.is_expired is True

    def test_release_rental_already_released(self, rental_service, mock_rental):
        """Test releasing already released rental."""
        mock_rental.is_expired = True

        with pytest.raises(RentalError):
            rental_service.release_rental(mock_rental)

    def test_get_rental_cost(self, rental_service):
        """Test getting rental cost."""
        cost = rental_service.get_rental_cost("whatsapp", "us", 24)

        assert cost > Decimal("0.00")
        assert isinstance(cost, Decimal)

    def test_get_rental_cost_invalid_service(self, rental_service):
        """Test getting cost for invalid service."""
        with pytest.raises(ValueError):
            rental_service.get_rental_cost("invalid", "us", 24)

    def test_get_rental_cost_invalid_country(self, rental_service):
        """Test getting cost for invalid country."""
        with pytest.raises(ValueError):
            rental_service.get_rental_cost("whatsapp", "invalid", 24)

    def test_calculate_extension_cost(self, rental_service, mock_rental):
        """Test calculating extension cost."""
        cost = rental_service.calculate_extension_cost(mock_rental, 12)

        assert cost > Decimal("0.00")
        assert isinstance(cost, Decimal)

    def test_get_available_services(self, rental_service):
        """Test getting available services."""
        services = rental_service.get_available_services("us")

        assert len(services) > 0
        assert "whatsapp" in services or "telegram" in services

    def test_get_available_countries(self, rental_service):
        """Test getting available countries."""
        countries = rental_service.get_available_countries()

        assert len(countries) > 0
        assert "us" in countries or "gb" in countries

    def test_validate_rental_data(self, rental_service):
        """Test rental data validation."""
        valid_data = {
            "service_name": "whatsapp",
            "country_code": "us",
            "duration_hours": 24
        }

        result = rental_service.validate_rental_data(valid_data)

        assert result is True

    def test_validate_rental_data_missing_field(self, rental_service):
        """Test rental data validation with missing field."""
        invalid_data = {
            "service_name": "whatsapp",
            "country_code": "us"
        }

        with pytest.raises(ValueError):
            rental_service.validate_rental_data(invalid_data)

    def test_get_rental_history(self, rental_service, mock_user):
        """Test getting rental history."""
        rentals = [mock_rental for _ in range(5)]

        with patch.object(rental_service.db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.order_by.return_value.all.return_value = rentals

            result = rental_service.get_rental_history(mock_user)

            assert len(result) == 5

    def test_get_rental_history_pagination(self, rental_service, mock_user):
        """Test rental history with pagination."""
        rentals = [mock_rental for _ in range(10)]

        with patch.object(rental_service.db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.order_by.return_value.limit.return_value.offset.return_value.all.return_value = rentals[:5]

            result = rental_service.get_rental_history(mock_user, page=1, limit=5)

            assert len(result) == 5

    def test_get_rental_statistics(self, rental_service, mock_user):
        """Test getting rental statistics."""
        stats = rental_service.get_rental_statistics(mock_user)

        assert stats is not None
        assert "total_rentals" in stats
        assert "active_rentals" in stats
        assert "total_spent" in stats

    def test_cancel_rental_success(self, rental_service, mock_rental):
        """Test successful rental cancellation."""
        mock_rental.is_expired = False

        result = rental_service.cancel_rental(mock_rental)

        assert result is not None
        assert result.is_expired is True

    def test_cancel_rental_already_expired(self, rental_service, mock_rental):
        """Test cancellation of already expired rental."""
        mock_rental.is_expired = True

        with pytest.raises(RentalError):
            rental_service.cancel_rental(mock_rental)
