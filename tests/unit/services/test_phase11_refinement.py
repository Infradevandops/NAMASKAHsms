from unittest.mock import MagicMock, patch

import pytest

from app.services.area_code_geo import NANPA_DATA, get_ranked_alternatives
from app.services.purchase_intelligence import PurchaseIntelligenceService


@pytest.mark.asyncio
async def test_geo_scaling_loads_json():
    """Verifies that AreaCodeGeo loads the new JSON index and performs ranking."""
    # Ensure our newly added Canadian code (416) exists in the loaded data
    assert "416" in NANPA_DATA
    assert NANPA_DATA["416"]["major_city"] == "Toronto"

    # Verify proximity ranking for a Canadian code (416 -> 647/437 should be same city)
    alts = await get_ranked_alternatives("416", "whatsapp")

    # First few should be same city (Toronto)
    cities = [a["city"] for a in alts[:2]]
    assert "Toronto" in cities


@pytest.mark.asyncio
async def test_carrier_enrichment_telemetry():
    """Verifies that carrier enrichment logic updates the database."""
    with patch("app.services.purchase_intelligence.SessionLocal") as mock_session_local:
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Call enrichment
        await PurchaseIntelligenceService.enrich_outcome_carrier(12345, "Verizon")

        # Verify SQL update was called
        # Note: enrichment happens in a background task, so we need a small wait or check call count
        import asyncio

        await asyncio.sleep(0.1)

        # Check if execute was called with an update statement
        assert mock_db.execute.called
        # Verify commit
        assert mock_db.commit.called
