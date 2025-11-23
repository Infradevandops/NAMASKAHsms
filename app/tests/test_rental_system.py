"""Tests for rental system functionality."""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from app.services.rental_service import RentalService


@pytest.fixture
def rental_data():
    return RentalCreate(
        service_name="whatsapp",
        country_code="us",
        duration_hours=24
    )


@pytest.fixture
def mock_user():
    user = AsyncMock()
    user.id = "user123"
    user.credits = Decimal("10.00")
    return user


@pytest.fixture
def mock_rental():
    rental = AsyncMock()
    rental.id = "rental123"
    rental.user_id = "user123"
    rental.phone_number = "+1234567890"
    rental.service_name = "whatsapp"
    rental.expires_at = datetime.utcnow() + timedelta(hours=24)
    rental.cost = Decimal("0.50")
    rental.is_expired = False
    rental.time_remaining_seconds = 86400
    return rental


class TestRentalService:

    @pytest.mark.asyncio
    async def test_create_rental_success(self, rental_data, mock_user):
        """Test successful rental creation."""
        db_mock = AsyncMock()
        service = RentalService(db_mock)

        with patch.object(service, '_get_user', return_value=mock_user), \
                patch('app.services.fivesim_service.FiveSimService') as mock_fivesim:

            mock_fivesim.return_value.buy_number.return_value = {
                'phone': '+1234567890',
                'id': 'activation123'
            }

            result = await service.create_rental("user123", rental_data)

            assert result is not None
            db_mock.add.assert_called_once()
            db_mock.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_rental_insufficient_credits(self, rental_data):
        """Test rental creation with insufficient credits."""
        db_mock = AsyncMock()
        service = RentalService(db_mock)

        poor_user = AsyncMock()
        poor_user.credits = Decimal("0.10")

        with patch.object(service, '_get_user', return_value=poor_user):
            with pytest.raises(InsufficientCreditsError):
                await service.create_rental("user123", rental_data)

    @pytest.mark.asyncio
    async def test_extend_rental_success(self, mock_user, mock_rental):
        """Test successful rental extension."""
        db_mock = AsyncMock()
        service = RentalService(db_mock)
        extend_data = RentalExtend(additional_hours=12)

        with patch.object(service, '_get_rental', return_value=mock_rental), \
                patch.object(service, '_get_user', return_value=mock_user):

            result = await service.extend_rental("rental123", "user123", extend_data)

            assert "extension_cost" in result
            assert result["extension_cost"] == 0.25  # 12 hours = 0.5 day * $0.50
            db_mock.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_rental_messages(self, mock_rental):
        """Test getting rental messages."""
        db_mock = AsyncMock()
        service = RentalService(db_mock)

        with patch.object(service, '_get_rental', return_value=mock_rental), \
                patch('app.services.fivesim_service.FiveSimService') as mock_fivesim:

            mock_fivesim.return_value.check_sms.return_value = {
                'sms': [{'text': 'Your code == 123456'}]
            }

            result = await service.get_rental_messages("rental123", "user123")

            assert result.phone_number == "+1234567890"
            assert result.message_count == 1
            assert "123456" in result.messages[0]
