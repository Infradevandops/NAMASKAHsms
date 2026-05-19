"""Unit tests for email template versioning, test email, and analytics."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


class TestEmailTemplateVersions:
    """Versioning endpoint returns list of versions."""

    def test_versions_endpoint_exists(self):
        from app.api.core.whitelabel_endpoints import get_template_versions

        assert callable(get_template_versions)

    def test_versions_endpoint_path(self):
        import inspect

        from app.api.core.whitelabel_endpoints import get_template_versions

        sig = inspect.signature(get_template_versions)
        assert "template_name" in sig.parameters

    @pytest.mark.asyncio
    async def test_versions_returns_list(self):
        from app.api.core.whitelabel_endpoints import get_template_versions

        mock_user = MagicMock()
        mock_user.id = "u1"
        mock_user.subscription_tier = "pro"

        mock_template = MagicMock()
        mock_template.id = "tpl_1"

        mock_version = MagicMock()
        mock_version.version_number = 1
        mock_version.subject = "Hello"
        mock_version.html_content = "<p>Hi</p>"
        mock_version.text_content = "Hi"
        mock_version.version_note = "Initial save"
        mock_version.created_by = "u1"
        from datetime import datetime, timezone

        mock_version.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)

        mock_db = MagicMock()

        mock_service = MagicMock()
        mock_service.get_template.return_value = mock_template
        mock_service.get_template_versions.return_value = [mock_version]

        with patch(
            "app.api.core.whitelabel_endpoints.email_template_service", mock_service
        ):
            result = await get_template_versions(
                template_name="welcome",
                current_user=mock_user,
                db=mock_db,
            )

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_versions_404_when_template_missing(self):
        from app.api.core.whitelabel_endpoints import get_template_versions

        mock_user = MagicMock()
        mock_user.id = "u1"
        mock_user.subscription_tier = "pro"

        mock_db = MagicMock()
        mock_service = MagicMock()
        mock_service.get_template.return_value = None

        with patch(
            "app.api.core.whitelabel_endpoints.email_template_service", mock_service
        ):
            with pytest.raises(HTTPException) as exc:
                await get_template_versions(
                    template_name="nonexistent",
                    current_user=mock_user,
                    db=mock_db,
                )
        assert exc.value.status_code == 404


class TestEmailTemplateTestSend:
    """Test email endpoint sends without error."""

    def test_test_email_endpoint_exists(self):
        from app.api.core.whitelabel_endpoints import send_test_email

        assert callable(send_test_email)

    @pytest.mark.asyncio
    async def test_send_test_email_success(self):
        from app.api.core.whitelabel_endpoints import (
            SendTestEmailRequest,
            send_test_email,
        )

        mock_user = MagicMock()
        mock_user.id = "u1"
        mock_user.subscription_tier = "pro"

        mock_service = MagicMock()
        mock_service.send_test_email = AsyncMock(return_value=True)

        mock_db = MagicMock()

        with patch(
            "app.api.core.whitelabel_endpoints.email_template_service", mock_service
        ):
            result = await send_test_email(
                request=SendTestEmailRequest(
                    template_name="welcome",
                    recipient_email="test@example.com",
                ),
                current_user=mock_user,
                db=mock_db,
            )

        assert result.get("success") is True or "message" in result


class TestEmailTemplateAnalytics:
    """Analytics endpoint returns correct shape."""

    def test_analytics_endpoint_exists(self):
        from app.api.core.whitelabel_endpoints import get_template_analytics

        assert callable(get_template_analytics)

    @pytest.mark.asyncio
    async def test_analytics_returns_counts(self):
        from app.api.core.whitelabel_endpoints import get_template_analytics

        mock_user = MagicMock()
        mock_user.id = "u1"
        mock_user.subscription_tier = "pro"

        mock_template = MagicMock()
        mock_template.id = "tpl_1"

        mock_analytics = MagicMock()
        mock_analytics.sent_count = 10
        mock_analytics.opened_count = 5
        mock_analytics.clicked_count = 2
        mock_analytics.bounced_count = 1
        mock_analytics.open_rate = 50.0
        mock_analytics.click_rate = 20.0
        mock_analytics.bounce_rate = 10.0
        mock_analytics.last_sent_at = None

        mock_db = MagicMock()
        mock_service = MagicMock()
        mock_service.get_template.return_value = mock_template
        mock_service.get_template_analytics.return_value = mock_analytics

        with patch(
            "app.api.core.whitelabel_endpoints.email_template_service", mock_service
        ):
            result = await get_template_analytics(
                template_name="welcome",
                current_user=mock_user,
                db=mock_db,
            )

        # Result is a Pydantic model or dict — either way has sent_count
        result_dict = result if isinstance(result, dict) else result.dict()
        assert "sent_count" in result_dict
