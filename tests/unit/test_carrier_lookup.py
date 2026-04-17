"""
Unit tests for CarrierLookupService (Phase 4 - Numverify Integration)
Tests real carrier verification via Numverify API
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.services.carrier_lookup import CarrierLookupService


class TestCarrierLookupBasics:
    """Test basic carrier lookup functionality"""

    def test_service_initialization_with_api_key(self):
        """Test service initializes when API key is present"""
        with patch.dict("os.environ", {"NUMVERIFY_API_KEY": "test_key"}):
            service = CarrierLookupService()
            assert service.enabled is True
            assert service.api_key == "test_key"

    def test_service_disabled_without_api_key(self):
        """Test service is disabled when API key is missing"""
        with patch.dict("os.environ", {}, clear=True):
            service = CarrierLookupService()
            assert service.enabled is False

    @pytest.mark.asyncio
    async def test_lookup_returns_carrier_info(self):
        """Test successful carrier lookup returns carrier name"""
        service = CarrierLookupService()
        service.enabled = True
        service.api_key = "test_key"

        mock_response = {
            "valid": True,
            "carrier": "Verizon Wireless",
            "line_type": "mobile",
        }

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200

            result = await service.lookup_carrier("+14155551234")

            assert result["success"] is True
            assert result["carrier"] == "verizon"  # Normalized
            assert result["raw_carrier"] == "Verizon Wireless"  # Original
            assert result["line_type"] == "mobile"
            assert result["valid"] is True


class TestCarrierLookupErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_disabled_service_returns_error(self):
        """Test disabled service returns error response"""
        service = CarrierLookupService()
        service.enabled = False

        result = await service.lookup_carrier("+14155551234")

        assert result["success"] is False
        assert "disabled" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_invalid_phone_number(self):
        """Test handling of invalid phone number"""
        service = CarrierLookupService()
        service.enabled = True
        service.api_key = "test_key"

        mock_response = {"valid": False, "error": {"info": "Invalid phone number"}}

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )
            mock_get.return_value.__aenter__.return_value.status = 200

            result = await service.lookup_carrier("invalid")

            assert result["success"] is False
            assert result["valid"] is False

    @pytest.mark.asyncio
    async def test_api_timeout_handling(self):
        """Test handling of API timeout"""
        service = CarrierLookupService()
        service.enabled = True
        service.api_key = "test_key"

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.side_effect = TimeoutError("Timeout")

            result = await service.lookup_carrier("+14155551234")

            assert result["success"] is False
            assert "timeout" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test handling of API errors"""
        service = CarrierLookupService()
        service.enabled = True
        service.api_key = "test_key"

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 500
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value="Server Error"
            )

            result = await service.lookup_carrier("+14155551234")

            assert result["success"] is False
            assert "error" in result


class TestCarrierNormalization:
    """Test carrier name normalization"""

    def test_normalize_verizon_variants(self):
        """Test normalization of Verizon carrier names"""
        service = CarrierLookupService()

        assert service.normalize_carrier("Verizon Wireless") == "verizon"
        assert service.normalize_carrier("VERIZON") == "verizon"
        assert service.normalize_carrier("verizon wireless") == "verizon"

    def test_normalize_tmobile_variants(self):
        """Test normalization of T-Mobile carrier names"""
        service = CarrierLookupService()

        assert service.normalize_carrier("T-Mobile USA") == "tmobile"
        assert service.normalize_carrier("T-Mobile") == "tmobile"
        assert service.normalize_carrier("TMOBILE") == "tmobile"

    def test_normalize_att_variants(self):
        """Test normalization of AT&T carrier names"""
        service = CarrierLookupService()

        assert service.normalize_carrier("AT&T Wireless") == "att"
        assert service.normalize_carrier("AT&T") == "att"
        assert service.normalize_carrier("ATT") == "att"

    def test_normalize_unknown_carrier(self):
        """Test normalization of unknown carrier"""
        service = CarrierLookupService()

        assert service.normalize_carrier("Unknown Carrier") == "unknown"
        assert service.normalize_carrier("") == "unknown"
        assert service.normalize_carrier(None) == "unknown"
