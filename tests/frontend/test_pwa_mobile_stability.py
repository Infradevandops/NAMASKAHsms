"""PWA installation, manifest, and mobile UI stability tests."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    import os

    os.environ.setdefault("TESTING", "1")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pwa-tests-min-32-chars")  # gitleaks:allow
    os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-key-for-pwa-tests-min-32-chars")  # gitleaks:allow
    from main import app

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


class TestPWAInstall:
    """Verify PWA is properly wired and installable."""

    def test_manifest_valid_json(self, client):
        r = client.get("/static/manifest.json")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "VRENUM SMS"
        assert data["display"] == "standalone"
        assert any(i["sizes"] == "512x512" for i in data["icons"])

    def test_manifest_has_ios_icon(self, client):
        r = client.get("/static/manifest.json")
        data = r.json()
        assert any(i["sizes"] == "180x180" for i in data["icons"])

    def test_service_worker_accessible(self, client):
        r = client.get("/static/js/service-worker.js")
        assert r.status_code == 200
        assert "CACHE_VERSION" in r.text

    def test_service_worker_has_offline_fallback(self, client):
        r = client.get("/static/js/service-worker.js")
        assert "navigate" in r.text
        assert "/offline" in r.text

    def test_offline_page(self, client):
        r = client.get("/offline")
        assert r.status_code == 200
        assert "offline" in r.text.lower()

    def test_icons_served(self, client):
        r = client.get("/static/icons/icon-192x192.png")
        assert r.status_code == 200
        assert len(r.content) > 100

    def test_icon_512_served(self, client):
        r = client.get("/static/icons/icon-512x512.png")
        assert r.status_code == 200
        assert len(r.content) > 100


class TestMobileUIStability:
    """Verify CSS rules that prevent overflow and mobile breakage."""

    def test_pwa_mobile_css_accessible(self, client):
        r = client.get("/static/css/pwa-mobile.css")
        assert r.status_code == 200

    def test_overflow_prevention(self, client):
        r = client.get("/static/css/pwa-mobile.css")
        assert "overflow-x: hidden" in r.text
        assert "overflow-wrap: break-word" in r.text

    def test_touch_action_present(self, client):
        r = client.get("/static/css/pwa-mobile.css")
        assert "touch-action: manipulation" in r.text

    def test_safe_area_insets(self, client):
        r = client.get("/static/css/pwa-mobile.css")
        assert "safe-area-inset" in r.text

    def test_ios_zoom_prevention(self, client):
        """iOS zooms on inputs with font-size < 16px."""
        r = client.get("/static/css/pwa-mobile.css")
        assert "font-size: 16px" in r.text

    def test_box_sizing_border_box(self, client):
        r = client.get("/static/css/pwa-mobile.css")
        assert "box-sizing: border-box" in r.text

    def test_small_phone_breakpoint(self, client):
        r = client.get("/static/css/pwa-mobile.css")
        assert "max-width: 375px" in r.text
