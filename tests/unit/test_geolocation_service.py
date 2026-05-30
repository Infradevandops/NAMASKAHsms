from unittest.mock import Mock

import pytest

from app.services.geolocation_service import GeolocationService


def test_detect_country_cloudflare():
    mock_request = Mock()
    mock_request.headers.get.side_effect = lambda k: (
        "NG" if k == "CF-IPCountry" else None
    )

    country = GeolocationService.detect_country(mock_request)
    assert country == "NG"


def test_detect_country_vercel():
    mock_request = Mock()
    mock_request.headers.get.side_effect = lambda k: (
        "IN" if k == "x-vercel-ip-country" else None
    )

    country = GeolocationService.detect_country(mock_request)
    assert country == "IN"


def test_detect_country_fallback():
    mock_request = Mock()
    mock_request.headers.get.return_value = None

    country = GeolocationService.detect_country(mock_request)
    assert country == "US"
