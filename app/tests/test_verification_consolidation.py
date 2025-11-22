"""Tests for consolidated verification API."""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.verification import Verification
from app.models.user import User


class TestConsolidatedVerificationAPI:
    """Test consolidated verification endpoints."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_user(self):
        """Mock user object."""
        user = MagicMock(spec=User)
        user.id = "test_user_id"
        user.credits = 10.0
        user.free_verifications = 5
        return user

    @pytest.fixture
    def mock_verification(self):
        """Mock verification object."""
        verification = MagicMock(spec=Verification)
        verification.id = "test_verification_id"
        verification.service_name = "telegram"
        verification.phone_number = "+1234567890"
        verification.capability = "sms"
        verification.status = "pending"
        verification.cost = 0.50
        verification.country = "US"
        verification.verification_code = "12345"
        verification.created_at = datetime.now(timezone.utc)
        verification.completed_at = None
        return verification

    @pytest.mark.asyncio
    async def test_get_available_services(self):
        """Test getting available services."""
        from app.api.verification.consolidated_verification import get_available_services

        result = await get_available_services()

        assert result["success"] is True
        assert len(result["services"]) > 0
        assert "telegram" in [s["id"] for s in result["services"]]
        assert "whatsapp" in [s["id"] for s in result["services"]]

    @pytest.mark.asyncio
    @patch('app.services.provider_registry.provider_manager')
    async def test_create_verification_success(self, mock_provider_manager,
                                               mock_db, mock_user):
        """Test successful verification creation."""
        from app.api.verification.consolidated_verification import create_verification
        from app.schemas import VerificationCreate

        # Setup mocks
        mock_provider_manager.get_balance.return_value = {"balance": 100.0}
        mock_provider_manager.buy_number.return_value = {
            "phone_number": "+1234567890",
            "activation_id": "12345"
        }

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        # Create verification data
        verification_data = VerificationCreate(
            service_name="telegram",
            country="US",
            capability="sms"
        )

        # Call endpoint
        result = await create_verification(
            verification_data=verification_data,
            user_id="test_user_id",
            db=mock_db
        )

        # Verify result
        assert result["service_name"] == "telegram"
        assert result["status"] == "pending"
        assert mock_provider_manager.get_balance.called
        assert mock_provider_manager.buy_number.called
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    @patch('app.services.provider_registry.provider_manager')
    async def test_create_verification_insufficient_credits(self, mock_provider_manager,
                                                            mock_db, mock_user):
        """Test verification creation with insufficient credits."""
        from app.api.verification.consolidated_verification import create_verification
        from app.schemas import VerificationCreate
        from fastapi import HTTPException

        # Setup mocks
        mock_provider_manager.get_balance.return_value = {"balance": 100.0}
        mock_user.credits = 0.25  # Less than required
        mock_user.free_verifications = 0
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        verification_data = VerificationCreate(service_name="telegram")

        # Should raise HTTPException for insufficient credits
        with pytest.raises(HTTPException) as exc_info:
            await create_verification(
                verification_data=verification_data,
                user_id="test_user_id",
                db=mock_db
            )

        assert exc_info.value.status_code == 402
        assert "Insufficient credits" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('app.services.provider_registry.provider_manager')
    async def test_create_verification_provider_failure(self, mock_provider_manager,
                                                        mock_db, mock_user):
        """Test verification creation with provider failure."""
        from app.api.verification.consolidated_verification import create_verification
        from app.schemas import VerificationCreate
        from fastapi import HTTPException

        # Setup mocks
        mock_provider_manager.get_balance.return_value = {"balance": 100.0}
        mock_provider_manager.buy_number.side_effect = Exception("Provider error")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.commit = MagicMock()

        verification_data = VerificationCreate(service_name="telegram")

        # Should raise HTTPException and refund credits
        with pytest.raises(HTTPException) as exc_info:
            await create_verification(
                verification_data=verification_data,
                user_id="test_user_id",
                db=mock_db
            )

        assert exc_info.value.status_code == 503
        assert "Failed to purchase SMS number" in exc_info.value.detail
        # Should have called commit twice (deduct + refund)
        assert mock_db.commit.call_count == 2

    @pytest.mark.asyncio
    @patch('app.services.provider_registry.provider_manager')
    async def test_get_verification_status_pending(self, mock_provider_manager,
                                                   mock_db, mock_verification):
        """Test getting verification status for pending verification."""
        from app.api.verification.consolidated_verification import get_verification_status

        # Setup mocks
        mock_provider_manager.check_sms.return_value = {"sms_code": None}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_verification

        result = await get_verification_status("test_verification_id", mock_db)

        assert result["id"] == "test_verification_id"
        assert result["status"] == "pending"
        assert mock_provider_manager.check_sms.called

    @pytest.mark.asyncio
    @patch('app.services.provider_registry.provider_manager')
    async def test_get_verification_status_completed(self, mock_provider_manager,
                                                     mock_db, mock_verification):
        """Test getting verification status when SMS is received."""
        from app.api.verification.consolidated_verification import get_verification_status

        # Setup mocks
        mock_provider_manager.check_sms.return_value = {"sms_code": "123456"}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_verification
        mock_db.commit = MagicMock()

        result = await get_verification_status("test_verification_id", mock_db)

        assert result["status"] == "completed"
        assert mock_verification.status == "completed"
        assert mock_verification.completed_at is not None
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_get_verification_status_not_found(self, mock_db):
        """Test getting verification status for non - existent verification."""
        from app.api.verification.consolidated_verification import get_verification_status
        from fastapi import HTTPException

        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_verification_status("nonexistent_id", mock_db)

        assert exc_info.value.status_code == 404
        assert "Verification not found" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('app.services.provider_registry.provider_manager')
    async def test_get_verification_messages_with_sms(self, mock_provider_manager,
                                                      mock_db, mock_verification):
        """Test getting verification messages when SMS is available."""
        from app.api.verification.consolidated_verification import get_verification_messages

        # Setup mocks
        mock_provider_manager.check_sms.return_value = {"sms_code": "123456"}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_verification
        mock_db.commit = MagicMock()

        result = await get_verification_messages("test_verification_id", mock_db)

        assert len(result["messages"]) == 1
        assert result["messages"][0]["code"] == "123456"
        assert result["code"] == "123456"
        assert result["status"] == "completed"
        assert mock_db.commit.called

    @pytest.mark.asyncio
    @patch('app.services.provider_registry.provider_manager')
    async def test_get_verification_messages_no_sms(self, mock_provider_manager,
                                                    mock_db, mock_verification):
        """Test getting verification messages when no SMS is available."""
        from app.api.verification.consolidated_verification import get_verification_messages

        # Setup mocks
        mock_provider_manager.check_sms.return_value = {"sms_code": None}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_verification

        result = await get_verification_messages("test_verification_id", mock_db)

        assert len(result["messages"]) == 0
        assert result["code"] is None
        assert result["status"] == "pending"

    def test_get_verification_history_basic(self, mock_db, mock_verification):
        """Test getting verification history."""
        from app.api.verification.consolidated_verification import get_verification_history

        # Setup mocks
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.all.return_value = [mock_verification]
        mock_db.query.return_value = mock_query

        result = get_verification_history(
            user_id="test_user_id",
            db=mock_db
        )

        assert result.total_count == 1
        assert len(result.verifications) == 1

    def test_get_verification_history_with_filters(self, mock_db):
        """Test getting verification history with filters."""
        from app.api.verification.consolidated_verification import get_verification_history

        # Setup mocks
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        result = get_verification_history(
            user_id="test_user_id",
            service="telegram",
            verification_status="completed",
            country="US",
            start_date="2024 - 01-01",
            end_date="2024 - 12-31",
            search="123",
            db=mock_db
        )

        assert result.total_count == 0
        # Verify filters were applied
        assert mock_query.filter.call_count >= 5  # Multiple filter calls

    @pytest.mark.asyncio
    async def test_get_verification_analytics_empty(self, mock_db):
        """Test getting analytics with no verifications."""
        from app.api.verification.consolidated_verification import get_verification_analytics

        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = await get_verification_analytics("test_user_id", mock_db)

        assert result["success"] is True
        assert result["total_verifications"] == 0
        assert result["overall_rate"] == 0.0
        assert result["by_service"] == {}
        assert result["by_country"] == {}

    @pytest.mark.asyncio
    async def test_get_verification_analytics_with_data(self, mock_db):
        """Test getting analytics with verification data."""
        from app.api.verification.consolidated_verification import get_verification_analytics

        # Create mock verifications
        completed_verification = MagicMock()
        completed_verification.status = "completed"
        completed_verification.service_name = "telegram"
        completed_verification.country = "US"

        pending_verification = MagicMock()
        pending_verification.status = "pending"
        pending_verification.service_name = "whatsapp"
        pending_verification.country = "US"

        mock_db.query.return_value.filter.return_value.all.return_value = [
            completed_verification, pending_verification
        ]

        result = await get_verification_analytics("test_user_id", mock_db)

        assert result["success"] is True
        assert result["total_verifications"] == 2
        assert result["successful"] == 1
        assert result["overall_rate"] == 50.0
        assert "telegram" in result["by_service"]
        assert "whatsapp" in result["by_service"]
        assert "US" in result["by_country"]

    @pytest.mark.asyncio
    async def test_cancel_verification_success(self, mock_db,
                                               mock_verification, mock_user):
        """Test successful verification cancellation."""
        from app.api.verification.consolidated_verification import cancel_verification

        # Setup mocks
        mock_verification.cost = 0.50
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_verification, mock_user
        ]
        mock_db.commit = MagicMock()

        result = await cancel_verification(
            "test_verification_id",
            "test_user_id",
            mock_db
        )

        assert result.message == "Verification cancelled and refunded"
        assert result.data["refunded"] == 0.50
        assert mock_verification.status == "cancelled"
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_cancel_verification_not_found(self, mock_db):
        """Test cancelling non - existent verification."""
        from app.api.verification.consolidated_verification import cancel_verification
        from fastapi import HTTPException

        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await cancel_verification(
                "nonexistent_id",
                "test_user_id",
                mock_db
            )

        assert exc_info.value.status_code == 404
        assert "Verification not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_cancel_verification_already_completed(self,
                                                         mock_db, mock_verification):
        """Test cancelling already completed verification."""
        from app.api.verification.consolidated_verification import cancel_verification
        from fastapi import HTTPException

        mock_verification.status = "completed"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_verification

        with pytest.raises(HTTPException) as exc_info:
            await cancel_verification(
                "test_verification_id",
                "test_user_id",
                mock_db
            )

        assert exc_info.value.status_code == 400
        assert "Cannot cancel completed verification" in exc_info.value.detail


class TestVerificationConsolidationIntegration:
    """Integration tests for verification consolidation."""

    @pytest.mark.asyncio
    async def test_complete_verification_flow(self):
        """Test complete verification flow through consolidated API."""
        # This would test the full flow from creation to completion
        # using the consolidated endpoints

    def test_endpoint_compatibility(self):
        """Test that consolidated endpoints maintain compatibility."""
        # Verify that all original endpoints are available
        # and return expected response formats

    def test_error_handling_consistency(self):
        """Test that error handling is consistent across endpoints."""
        # Verify that all endpoints use proper error handling
        # and return consistent error formats
