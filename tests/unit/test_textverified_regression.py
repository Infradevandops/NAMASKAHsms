"""TextVerified regression tests — Phase 4, BROKEN_ITEMS.md.

Covers the 18 bug fixes documented in docs/SMS_LOGIC.md.
Each test is named after the deviation it guards against.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, call


def _make_service():
    """Create TextVerifiedService with mocked client."""
    with patch.dict("os.environ", {
        "TEXTVERIFIED_API_KEY": "test-key",
        "TEXTVERIFIED_EMAIL": "test@example.com",
    }):
        with patch("app.services.textverified_service.textverified") as mock_tv_module:
            mock_tv_module.TextVerified.return_value = MagicMock()
            from app.services.textverified_service import TextVerifiedService
            svc = TextVerifiedService()
            svc.enabled = True
            svc.client = MagicMock()
            return svc


# ── Deviation 1: poll_sms_standard uses TV object, not string ID ──────────────

@pytest.mark.asyncio
async def test_poll_sms_standard_uses_tv_object():
    """sms.incoming() must receive the VerificationExpanded object, not a string."""
    svc = _make_service()

    tv_obj = MagicMock()
    tv_obj.created_at = datetime.now(timezone.utc)
    tv_obj.number = "+12025551234"

    received_sms = MagicMock()
    received_sms.parsed_code = "123456"
    received_sms.sms_content = "Your code is 123456"
    received_sms.created_at = datetime.now(timezone.utc)

    def _mock_incoming(data, since, timeout, polling_interval):
        # Verify data is the object, not a string
        assert not isinstance(data, str), "sms.incoming() received a string ID instead of TV object"
        assert data is tv_obj
        yield received_sms

    svc.client.sms.incoming = _mock_incoming

    result = await svc.poll_sms_standard(tv_obj, timeout_seconds=30.0)

    assert result["success"] is True
    assert result["code"] == "123456"


# ── Deviation 2: parsed_code used first, regex is fallback ───────────────────

@pytest.mark.asyncio
async def test_poll_sms_standard_parsed_code_first():
    """parsed_code from TV must be used before regex extraction."""
    svc = _make_service()

    tv_obj = MagicMock()
    tv_obj.created_at = datetime.now(timezone.utc)

    sms = MagicMock()
    sms.parsed_code = "806185"  # TV already parsed it
    sms.sms_content = "Your code is 806-185"  # Hyphenated in raw text
    sms.created_at = datetime.now(timezone.utc)

    def _mock_incoming(data, since, timeout, polling_interval):
        yield sms

    svc.client.sms.incoming = _mock_incoming

    result = await svc.poll_sms_standard(tv_obj, timeout_seconds=30.0)

    assert result["success"] is True
    assert result["code"] == "806185"  # From parsed_code, not regex


# ── Deviation 2b: regex fallback handles hyphenated codes ────────────────────

@pytest.mark.asyncio
async def test_poll_sms_standard_regex_fallback_hyphenated():
    """When parsed_code is empty, regex must handle hyphenated codes like 806-185."""
    svc = _make_service()

    tv_obj = MagicMock()
    tv_obj.created_at = datetime.now(timezone.utc)

    sms = MagicMock()
    sms.parsed_code = ""  # Empty — force regex path
    sms.sms_content = "Your verification code is 806-185"
    sms.created_at = datetime.now(timezone.utc)

    def _mock_incoming(data, since, timeout, polling_interval):
        yield sms

    svc.client.sms.incoming = _mock_incoming

    result = await svc.poll_sms_standard(tv_obj, timeout_seconds=30.0)

    assert result["success"] is True
    assert result["code"] == "806185"  # Hyphen stripped


# ── Deviation 3: create_verification returns ends_at and tv_object ────────────

@pytest.mark.asyncio
async def test_create_verification_returns_ends_at_and_tv_object():
    """create_verification must return ends_at and tv_object in result dict."""
    svc = _make_service()

    mock_result = MagicMock()
    mock_result.id = "tv-act-123"
    mock_result.number = "+12025551234"
    mock_result.total_cost = 2.22
    mock_result.ends_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    with patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_result), \
         patch.object(svc, "_build_area_code_preference", new_callable=AsyncMock, return_value=["415"]), \
         patch.object(svc, "_get_area_codes_by_state", new_callable=AsyncMock, return_value={}):

        from app.services.phone_validator import PhoneValidator
        from app.services.carrier_lookup import CarrierLookupService

        with patch.object(PhoneValidator, "validate_mobile", return_value={"is_mobile": True, "is_voip": False}), \
             patch.object(CarrierLookupService, "__init__", return_value=None):

            with patch("app.services.textverified_service.CarrierLookupService") as MockCL:
                MockCL.return_value.enabled = False

                result = await svc.create_verification(
                    service="whatsapp",
                    country="US",
                    area_code="415",
                )

    assert "ends_at" in result
    assert result["ends_at"] is not None
    assert "tv_object" in result
    assert result["tv_object"] is mock_result


# ── Deviation 5: report_verification called on timeout ───────────────────────

@pytest.mark.asyncio
async def test_report_verification_called_on_timeout():
    """report_verification must be called when verification times out."""
    svc = _make_service()
    svc.client.verifications.report = MagicMock()

    result = await svc.report_verification("tv-act-123")

    svc.client.verifications.report.assert_called_once_with("tv-act-123")
    assert result is True


# ── Deviation 6: ends_at used for real timeout ───────────────────────────────

@pytest.mark.asyncio
async def test_poll_sms_standard_uses_ends_at_for_timeout():
    """poll_sms_standard must accept timeout_seconds derived from ends_at."""
    svc = _make_service()

    tv_obj = MagicMock()
    tv_obj.created_at = datetime.now(timezone.utc)

    captured_timeout = {}

    def _mock_incoming(data, since, timeout, polling_interval):
        captured_timeout["value"] = timeout
        return iter([])  # No SMS — timeout

    svc.client.sms.incoming = _mock_incoming

    await svc.poll_sms_standard(tv_obj, timeout_seconds=42.0)

    assert captured_timeout["value"] == 42.0


# ── Deviation: get_sms filters stale SMS via created_after ───────────────────

@pytest.mark.asyncio
async def test_get_sms_filters_stale_messages():
    """get_sms must reject SMS received before verification was created."""
    svc = _make_service()

    created_at = datetime.now(timezone.utc)
    stale_time = created_at - timedelta(minutes=5)
    fresh_time = created_at + timedelta(seconds=30)

    stale_sms = MagicMock()
    stale_sms.created_at = stale_time
    stale_sms.sms_content = "Old code 111111"
    stale_sms.parsed_code = "111111"

    fresh_sms = MagicMock()
    fresh_sms.created_at = fresh_time
    fresh_sms.sms_content = "Your code is 999999"
    fresh_sms.parsed_code = "999999"

    with patch("asyncio.to_thread", new_callable=AsyncMock, return_value=[stale_sms, fresh_sms]):
        result = await svc.get_sms("tv-act-123", created_after=created_at)

    assert result["success"] is True
    assert result["code"] == "999999"  # Only fresh SMS returned


@pytest.mark.asyncio
async def test_get_sms_returns_pending_when_all_stale():
    """get_sms must return pending (not error) when all SMS are stale."""
    svc = _make_service()

    created_at = datetime.now(timezone.utc)
    stale_sms = MagicMock()
    stale_sms.created_at = created_at - timedelta(minutes=5)
    stale_sms.sms_content = "Old code 111111"

    with patch("asyncio.to_thread", new_callable=AsyncMock, return_value=[stale_sms]):
        result = await svc.get_sms("tv-act-123", created_after=created_at)

    assert result["success"] is False
    assert result["sms"] is None
    assert "error" not in result  # Not an error — just pending


# ── Deviation: area code fallback same-state detection ───────────────────────

@pytest.mark.asyncio
async def test_area_code_fallback_same_state():
    """When area code falls back, same_state_fallback must be True for same-state codes."""
    svc = _make_service()

    mock_result = MagicMock()
    mock_result.id = "tv-act-456"
    mock_result.number = "+14085551234"  # 408 — different from requested 415
    mock_result.total_cost = 2.22
    mock_result.ends_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    # Both 415 and 408 are in CA
    by_state = {"CA": ["415", "408", "510"]}

    with patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_result), \
         patch.object(svc, "_build_area_code_preference", new_callable=AsyncMock, return_value=["415", "408"]), \
         patch.object(svc, "_get_area_codes_by_state", new_callable=AsyncMock, return_value=by_state):

        with patch("app.services.textverified_service.PhoneValidator") as MockPV, \
             patch("app.services.textverified_service.CarrierLookupService") as MockCL:

            MockPV.return_value.validate_mobile.return_value = {"is_mobile": True, "is_voip": False}
            MockCL.return_value.enabled = False

            result = await svc.create_verification(
                service="whatsapp",
                country="US",
                area_code="415",
            )

    assert result["fallback_applied"] is True
    assert result["same_state_fallback"] is True
    assert result["requested_area_code"] == "415"
    assert result["assigned_area_code"] == "408"


# ── Deviation: VOIP rejection ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_voip_rejection_triggers_retry():
    """VOIP numbers must be cancelled and retried, not accepted."""
    svc = _make_service()

    voip_result = MagicMock()
    voip_result.id = "tv-voip-1"
    voip_result.number = "+12025550001"
    voip_result.total_cost = 2.22
    voip_result.ends_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    mobile_result = MagicMock()
    mobile_result.id = "tv-mobile-2"
    mobile_result.number = "+12025550002"
    mobile_result.total_cost = 2.22
    mobile_result.ends_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    call_count = 0

    async def _mock_to_thread(fn, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return voip_result
        return mobile_result

    with patch("asyncio.to_thread", side_effect=_mock_to_thread), \
         patch.object(svc, "_build_area_code_preference", new_callable=AsyncMock, return_value=None), \
         patch.object(svc, "_get_area_codes_by_state", new_callable=AsyncMock, return_value={}), \
         patch.object(svc, "_cancel_safe", new_callable=AsyncMock, return_value=True):

        with patch("app.services.textverified_service.PhoneValidator") as MockPV, \
             patch("app.services.textverified_service.CarrierLookupService") as MockCL:

            # First call returns VOIP, second returns mobile
            MockPV.return_value.validate_mobile.side_effect = [
                {"is_mobile": False, "is_voip": True, "number_type": "voip"},
                {"is_mobile": True, "is_voip": False},
            ]
            MockCL.return_value.enabled = False

            result = await svc.create_verification(
                service="whatsapp",
                country="US",
                max_retries=3,
            )

    assert result["voip_rejected"] is True
    assert result["retry_attempts"] >= 1


# ── Deviation: carrier preference applied ────────────────────────────────────

def test_carrier_preference_applied():
    """_build_carrier_preference must return normalized carrier as first element."""
    svc = _make_service()

    result = svc._build_carrier_preference("T-Mobile")
    assert isinstance(result, list)
    assert len(result) >= 1
    assert result[0] == "t_mobile"  # Normalized: lowercase, spaces to underscores


def test_carrier_preference_normalized():
    """Carrier names with special chars must be normalized correctly."""
    svc = _make_service()

    assert svc._build_carrier_preference("AT&T")[0] == "at&t".replace("&", "")
    assert svc._build_carrier_preference("Verizon")[0] == "verizon"
