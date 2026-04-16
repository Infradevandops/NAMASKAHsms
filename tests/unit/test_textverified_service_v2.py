"""Unit tests for TextVerifiedService V2 enhancements."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.textverified_service import TextVerifiedService


@pytest.mark.asyncio
async def test_build_area_code_preference_chain():
    """Test that area code proximity chain is built correctly."""
    service = TextVerifiedService()

    # Mock the live area codes index
    mock_codes = [
        {"area_code": "212", "state": "NY"},
        {"area_code": "718", "state": "NY"},
        {"area_code": "917", "state": "NY"},
        {"area_code": "415", "state": "CA"},
        {"area_code": "650", "state": "CA"},
    ]

    with patch.object(
        service, "get_area_codes_list", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = mock_codes

        # Test NY chain
        chain = await service._build_area_code_preference("212")
        # Requested 212 should be first, followed by NY siblings
        assert chain[0] == "212"
        assert set(chain) == {"212", "718", "917"}
        assert len(chain) == 3

        # Test unknown code
        chain_unknown = await service._build_area_code_preference("999")
        assert chain_unknown == ["999"]


def test_build_carrier_preference():
    """Test carrier preference normalization."""
    service = TextVerifiedService()

    # TextVerified expects lowercase/underscored carrier names usually,
    # but we ensure it's a list with one item for strict enforcement.
    assert service._build_carrier_preference("Verizon") == ["verizon"]
    assert service._build_carrier_preference("T-Mobile") == ["t-mobile"]
    assert service._build_carrier_preference("AT & T") == ["at__t"]


@pytest.mark.asyncio
async def test_create_verification_with_fallback_tracking():
    """Test create_verification tracks fallback and carrier correctly."""
    service = TextVerifiedService()
    service.enabled = True
    service.client = MagicMock()

    # Mock result from TextVerified client
    mock_result = MagicMock()
    mock_result.id = "tv_123"
    mock_result.number = "+14155550199"
    mock_result.total_cost = 1.50

    with patch.object(
        service, "_build_area_code_preference", new_callable=AsyncMock
    ) as mock_pref:
        mock_pref.return_value = ["212", "718", "917"]

        with patch.object(
            service, "_get_area_codes_by_state", new_callable=AsyncMock
        ) as mock_by_state:
            # Mock index for same-state check
            mock_by_state.return_value = {
                "NY": ["212", "718", "917"],
                "CA": ["415", "650"],
            }

            with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_thread:
                mock_thread.return_value = mock_result

                # Request 212, Get 415 (Different State)
                result = await service.create_verification(
                    service="telegram", area_code="212"
                )

                assert result["id"] == "tv_123"
                assert result["fallback_applied"] is True
                assert result["assigned_area_code"] == "415"
                assert result["same_state_fallback"] is False  # NY -> CA

                # Request 415, Get 650 (Same State)
                mock_result.number = "+16505550199"
                mock_thread.return_value = mock_result
                mock_pref.return_value = ["415", "650"]

                result_same = await service.create_verification(
                    service="telegram", area_code="415"
                )
                assert result_same["fallback_applied"] is True
                assert result_same["assigned_area_code"] == "650"
                assert result_same["same_state_fallback"] is True  # CA -> CA
