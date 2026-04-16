"""
Unit tests for RefundService (Phase 5 - Tier-Aware Refunds)
Tests automatic refund logic for filter mismatches
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from app.services.refund_service import RefundService


class TestRefundServiceBasics:
    """Test basic refund service functionality"""

    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test RefundService can be instantiated"""
        service = RefundService()
        assert service is not None

    @pytest.mark.asyncio
    async def test_no_refund_when_all_matched(self):
        """Test no refund when area code and carrier both match"""
        service = RefundService()

        verification = Mock(
            id="ver_123",
            user_id="user_123",
            area_code_matched=True,
            carrier_matched=True,
            area_code_surcharge=0.25,
            carrier_surcharge=0.30,
            cost=3.00,
        )
        user = Mock(subscription_tier="payg", credits=10.0)

        result = await service.process_refund(verification, user, Mock())

        assert result["refund_issued"] is False
        assert result["refund_amount"] == 0.0
        assert result["reason"] == "no_mismatch"


class TestPaygRefunds:
    """Test PAYG tier refund logic"""

    @pytest.mark.asyncio
    async def test_payg_area_code_mismatch_refund(self):
        """Test PAYG user gets area code surcharge refund"""
        service = RefundService()

        verification = Mock(
            id="ver_123",
            user_id="user_123",
            area_code_matched=False,
            carrier_matched=True,
            area_code_surcharge=0.25,
            carrier_surcharge=0.0,
            cost=3.00,
        )
        user = Mock(subscription_tier="payg", credits=10.0)
        db = Mock()

        result = await service.process_refund(verification, user, db)

        assert result["refund_issued"] is True
        assert result["refund_amount"] == 0.25
        assert result["refund_type"] == "surcharge"
        assert "area_code" in result["reason"]
        assert user.credits == 10.25  # Refunded

    @pytest.mark.asyncio
    async def test_payg_carrier_mismatch_refund(self):
        """Test PAYG user gets carrier surcharge refund"""
        service = RefundService()

        verification = Mock(
            id="ver_123",
            user_id="user_123",
            area_code_matched=True,
            carrier_matched=False,
            area_code_surcharge=0.0,
            carrier_surcharge=0.30,
            cost=3.00,
        )
        user = Mock(subscription_tier="payg", credits=10.0)
        db = Mock()

        result = await service.process_refund(verification, user, db)

        assert result["refund_issued"] is True
        assert result["refund_amount"] == 0.30
        assert result["refund_type"] == "surcharge"
        assert "carrier" in result["reason"]
        assert user.credits == 10.30

    @pytest.mark.asyncio
    async def test_payg_both_mismatch_refund(self):
        """Test PAYG user gets both surcharges refunded"""
        service = RefundService()

        verification = Mock(
            id="ver_123",
            user_id="user_123",
            area_code_matched=False,
            carrier_matched=False,
            area_code_surcharge=0.25,
            carrier_surcharge=0.30,
            cost=3.00,
        )
        user = Mock(subscription_tier="payg", credits=10.0)
        db = Mock()

        result = await service.process_refund(verification, user, db)

        assert result["refund_issued"] is True
        assert result["refund_amount"] == 0.55  # 0.25 + 0.30
        assert result["refund_type"] == "surcharge"
        assert user.credits == 10.55


class TestProCustomRefunds:
    """Test Pro/Custom tier refund logic"""

    @pytest.mark.asyncio
    async def test_pro_area_code_mismatch_no_surcharge_refund(self):
        """Test Pro user doesn't get surcharge refund (filters included)"""
        service = RefundService()

        verification = Mock(
            id="ver_123",
            user_id="user_123",
            area_code_matched=False,
            carrier_matched=True,
            area_code_surcharge=0.0,  # Pro doesn't pay surcharge
            carrier_surcharge=0.0,
            cost=0.30,  # Overage rate
        )
        user = Mock(subscription_tier="pro", credits=10.0)
        db = Mock()

        result = await service.process_refund(verification, user, db)

        assert result["refund_issued"] is True
        assert result["refund_amount"] == 0.30  # Full overage refund
        assert result["refund_type"] == "overage"
        assert user.credits == 10.30

    @pytest.mark.asyncio
    async def test_custom_carrier_mismatch_overage_refund(self):
        """Test Custom user gets overage refund"""
        service = RefundService()

        verification = Mock(
            id="ver_123",
            user_id="user_123",
            area_code_matched=True,
            carrier_matched=False,
            area_code_surcharge=0.0,
            carrier_surcharge=0.0,
            cost=0.20,  # Custom overage rate
        )
        user = Mock(subscription_tier="custom", credits=10.0)
        db = Mock()

        result = await service.process_refund(verification, user, db)

        assert result["refund_issued"] is True
        assert result["refund_amount"] == 0.20
        assert result["refund_type"] == "overage"
        assert user.credits == 10.20

    @pytest.mark.asyncio
    async def test_pro_both_mismatch_overage_refund(self):
        """Test Pro user gets single overage refund for both mismatches"""
        service = RefundService()

        verification = Mock(
            id="ver_123",
            user_id="user_123",
            area_code_matched=False,
            carrier_matched=False,
            area_code_surcharge=0.0,
            carrier_surcharge=0.0,
            cost=0.30,
        )
        user = Mock(subscription_tier="pro", credits=10.0)
        db = Mock()

        result = await service.process_refund(verification, user, db)

        assert result["refund_issued"] is True
        assert result["refund_amount"] == 0.30  # Single overage refund
        assert result["refund_type"] == "overage"


class TestFreemiumRefunds:
    """Test Freemium tier refund logic"""

    @pytest.mark.asyncio
    async def test_freemium_no_refund(self):
        """Test Freemium users don't get refunds (no filters available)"""
        service = RefundService()

        verification = Mock(
            id="ver_123",
            user_id="user_123",
            area_code_matched=False,
            carrier_matched=False,
            area_code_surcharge=0.0,
            carrier_surcharge=0.0,
            cost=2.22,
        )
        user = Mock(subscription_tier="freemium", credits=10.0)
        db = Mock()

        result = await service.process_refund(verification, user, db)

        assert result["refund_issued"] is False
        assert result["refund_amount"] == 0.0
        assert result["reason"] == "freemium_no_filters"
        assert user.credits == 10.0  # No change


class TestRefundTracking:
    """Test refund tracking and audit trail"""

    @pytest.mark.asyncio
    async def test_refund_creates_transaction_record(self):
        """Test refund creates transaction record in database"""
        service = RefundService()

        verification = Mock(
            id="ver_123",
            user_id="user_123",
            area_code_matched=False,
            carrier_matched=False,
            area_code_surcharge=0.25,
            carrier_surcharge=0.30,
            cost=3.00,
        )
        user = Mock(subscription_tier="payg", credits=10.0)

        mock_db = Mock()
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()

        result = await service.process_refund(verification, user, mock_db)

        assert result["refund_issued"] is True
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_refund_includes_metadata(self):
        """Test refund result includes detailed metadata"""
        service = RefundService()

        verification = Mock(
            id="ver_123",
            user_id="user_123",
            area_code_matched=False,
            carrier_matched=True,
            area_code_surcharge=0.25,
            carrier_surcharge=0.0,
            cost=3.00,
        )
        user = Mock(subscription_tier="payg", credits=10.0)
        db = Mock()

        result = await service.process_refund(verification, user, db)

        assert "refund_issued" in result
        assert "refund_amount" in result
        assert "refund_type" in result
        assert "reason" in result
        assert "timestamp" in result
