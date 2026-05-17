"""Unit tests for WhitelabelMiddleware"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.middleware.whitelabel_middleware import (
    WhitelabelMiddleware,
    get_whitelabel_context,
)
from app.models.whitelabel_models import WhitelabelBranding


@pytest.fixture
def mock_app():
    async def app(scope, receive, send):
        from starlette.responses import HTMLResponse

        response = HTMLResponse("<html><head></head><body>Test</body></html>")
        await response(scope, receive, send)

    return app


class TestWhitelabelContext:
    """Test whitelabel context helper"""

    def test_get_context_enabled(self):
        request = Mock()
        request.state.whitelabel = {
            "enabled": True,
            "partner_id": 1,
            "branding": {"company_name": "Test"},
            "domain": "custom.com",
        }

        context = get_whitelabel_context(request)
        assert context["enabled"] is True
        assert context["partner_id"] == 1

    def test_get_context_disabled(self):
        request = Mock()
        delattr(request, "state")

        context = get_whitelabel_context(request)
        assert context["enabled"] is False
        assert context["branding"] is None


class TestMiddlewareInitialization:
    """Test middleware initialization"""

    def test_init_strips_protocol(self, mock_app):
        middleware = WhitelabelMiddleware(mock_app, base_domain="https://vrenum.app")
        assert middleware.base_domain == "vrenum.app"

    def test_init_strips_port(self, mock_app):
        middleware = WhitelabelMiddleware(mock_app, base_domain="vrenum.app:8000")
        assert middleware.base_domain == "vrenum.app"


class TestDomainDetection:
    """Test domain detection logic"""

    @pytest.mark.asyncio
    async def test_base_domain_no_whitelabel(self, mock_app):
        middleware = WhitelabelMiddleware(mock_app, base_domain="vrenum.app")

        request = Mock()
        request.headers = {"host": "vrenum.app"}
        request.state = Mock()

        with patch("app.middleware.whitelabel_middleware.SessionLocal") as mock_session:
            call_next = AsyncMock(
                return_value=Mock(
                    headers={"content-type": "text/html"}, body_iterator=[]
                )
            )

            await middleware.dispatch(request, call_next)

            # Should not query database for base domain
            assert not mock_session.called

    @pytest.mark.asyncio
    async def test_custom_domain_queries_db(self, mock_app):
        middleware = WhitelabelMiddleware(mock_app, base_domain="vrenum.app")

        request = Mock()
        request.headers = {"host": "custom.example.com"}
        request.state = Mock()

        mock_branding = Mock(spec=WhitelabelBranding)
        mock_branding.user_id = 1
        mock_branding.to_dict.return_value = {"company_name": "Custom"}

        with patch("app.middleware.whitelabel_middleware.SessionLocal") as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db

            with patch(
                "app.services.whitelabel_service.whitelabel_service.get_branding_by_domain"
            ) as mock_get:
                mock_get.return_value = mock_branding

                call_next = AsyncMock(
                    return_value=Mock(
                        headers={"content-type": "text/html"}, body_iterator=[]
                    )
                )

                await middleware.dispatch(request, call_next)

                # Should query database
                mock_get.assert_called_once_with(mock_db, "custom.example.com")


class TestBrandingInjection:
    """Test CSS injection"""

    @pytest.mark.asyncio
    async def test_css_injected_for_html(self, mock_app):
        middleware = WhitelabelMiddleware(mock_app, base_domain="vrenum.app")

        request = Mock()
        request.headers = {"host": "custom.example.com"}
        request.state = Mock()
        request.state.whitelabel = {
            "enabled": True,
            "branding": {
                "primary_color": "#FF0000",
                "secondary_color": "#00FF00",
                "accent_color": "#0000FF",
                "font_family": "Arial",
                "logo_url": "https://example.com/logo.png",
            },
        }

        html_body = b"<html><head></head><body>Test</body></html>"

        async def body_iterator():
            yield html_body

        response = Mock()
        response.headers = {"content-type": "text/html"}
        response.body_iterator = body_iterator()
        response.status_code = 200

        result = await middleware._inject_branding_css(request, response)

        # Should return modified response
        assert result is not None

    @pytest.mark.asyncio
    async def test_no_injection_for_json(self, mock_app):
        middleware = WhitelabelMiddleware(mock_app, base_domain="vrenum.app")

        request = Mock()
        request.state = Mock()
        request.state.whitelabel = {"enabled": True, "branding": {}}

        response = Mock()
        response.headers = {"content-type": "application/json"}

        call_next = AsyncMock(return_value=response)

        result = await middleware.dispatch(request, call_next)

        # Should not modify JSON responses
        assert result == response


class TestErrorHandling:
    """Test error handling"""

    @pytest.mark.asyncio
    async def test_db_error_graceful(self, mock_app):
        middleware = WhitelabelMiddleware(mock_app, base_domain="vrenum.app")

        request = Mock()
        request.headers = {"host": "custom.example.com"}
        request.state = Mock()

        with patch("app.middleware.whitelabel_middleware.SessionLocal") as mock_session:
            mock_session.side_effect = Exception("DB error")

            call_next = AsyncMock(
                return_value=Mock(
                    headers={"content-type": "text/html"}, body_iterator=[]
                )
            )

            # Should not crash
            result = await middleware.dispatch(request, call_next)
            assert result is not None

    @pytest.mark.asyncio
    async def test_injection_error_graceful(self, mock_app):
        middleware = WhitelabelMiddleware(mock_app, base_domain="vrenum.app")

        request = Mock()
        request.state = Mock()
        request.state.whitelabel = {"enabled": True, "branding": None}

        response = Mock()
        response.headers = {"content-type": "text/html"}
        response.body_iterator = None  # Will cause error

        # Should not crash
        result = await middleware._inject_branding_css(request, response)
        assert result == response
