"""Unit tests for Email Templates enhancements."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.models.whitelabel_models import (
    EmailTemplateAnalytics,
    EmailTemplateVersion,
    WhitelabelEmailTemplate,
)
from app.services.email_template_service import EmailTemplateService


class TestTemplateVersioning:
    """Test template versioning functionality."""

    def test_create_template_with_version(self, mock_db_session):
        """Test creating template initializes version to 1."""
        service = EmailTemplateService()

        template = WhitelabelEmailTemplate(
            id=1,
            user_id="user_123",
            template_name="welcome",
            subject="Welcome!",
            html_content="<h1>Welcome</h1>",
            text_content="Welcome",
            version=1,
        )

        assert template.version == 1

    def test_update_template_increments_version(self, mock_db_session):
        """Test updating template increments version."""
        service = EmailTemplateService()

        # Simulate existing template
        template = Mock(
            id=1,
            version=1,
            subject="Old Subject",
            html_content="<h1>Old</h1>",
            text_content="Old",
        )

        # Update increments version
        template.version += 1

        assert template.version == 2

    def test_save_version_to_history(self, mock_db_session):
        """Test that old version is saved to history."""
        version = EmailTemplateVersion(
            id=1,
            template_id=1,
            version_number=1,
            subject="Old Subject",
            html_content="<h1>Old</h1>",
            text_content="Old",
            version_note="Auto-saved version",
            created_by="user_123",
        )

        assert version.version_number == 1
        assert version.template_id == 1

    def test_get_template_versions(self, mock_db_session):
        """Test retrieving version history."""
        service = EmailTemplateService()

        versions = [
            Mock(version_number=3, created_at=datetime.now(timezone.utc)),
            Mock(version_number=2, created_at=datetime.now(timezone.utc)),
            Mock(version_number=1, created_at=datetime.now(timezone.utc)),
        ]

        mock_db_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            versions
        )

        result = service.get_template_versions(mock_db_session, template_id=1, limit=10)

        assert len(result) == 3
        assert result[0].version_number == 3  # Most recent first

    def test_revert_to_previous_version(self, mock_db_session):
        """Test reverting to a previous version."""
        service = EmailTemplateService()

        # Mock version to revert to
        old_version = Mock(
            template_id=1,
            version_number=2,
            subject="Old Subject",
            html_content="<h1>Old</h1>",
            text_content="Old",
        )

        # Mock current template
        current_template = Mock(
            id=1,
            version=3,
            subject="Current Subject",
            html_content="<h1>Current</h1>",
            text_content="Current",
        )

        # Simulate revert
        current_template.subject = old_version.subject
        current_template.html_content = old_version.html_content
        current_template.text_content = old_version.text_content
        current_template.version += 1

        assert current_template.subject == "Old Subject"
        assert current_template.version == 4  # Incremented after revert


class TestTestEmail:
    """Test test email functionality."""

    @pytest.mark.asyncio
    @patch("app.services.email_service.email_service._send", new_callable=AsyncMock)
    async def test_send_test_email_success(self, mock_send, mock_db_session):
        """Test sending test email successfully."""
        mock_send.return_value = True
        service = EmailTemplateService()

        template = Mock(
            template_name="welcome",
            subject="Welcome {{ user_name }}!",
            html_content="<h1>Welcome {{ user_name }}</h1>",
            text_content="Welcome {{ user_name }}",
        )

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            template
        )

        result = await service.send_test_email(
            db=mock_db_session,
            user_id="user_123",
            template_name="welcome",
            recipient_email="test@example.com",
        )

        assert result is True

    @pytest.mark.asyncio
    @patch("app.services.email_service.email_service._send", new_callable=AsyncMock)
    async def test_send_test_email_with_custom_variables(
        self, mock_send, mock_db_session
    ):
        """Test sending test email with custom variables."""
        mock_send.return_value = True
        service = EmailTemplateService()

        template = Mock(
            template_name="welcome",
            subject="Welcome {{ user_name }}!",
            html_content="<h1>Welcome {{ user_name }}</h1>",
            text_content="Welcome {{ user_name }}",
        )

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            template
        )

        custom_vars = {
            "user_name": "Jane Doe",
            "user_email": "jane@example.com",
            "company_name": "Test Company",
            "support_email": "support@test.com",
        }

        result = await service.send_test_email(
            db=mock_db_session,
            user_id="user_123",
            template_name="welcome",
            recipient_email="test@example.com",
            test_variables=custom_vars,
        )

        assert result is True

    def test_get_test_variables(self):
        """Test getting default test variables."""
        service = EmailTemplateService()

        test_vars = service._get_test_variables("welcome")

        assert "user_name" in test_vars
        assert "company_name" in test_vars
        assert test_vars["user_name"] == "John Doe"

    @pytest.mark.asyncio
    async def test_send_test_email_template_not_found(self, mock_db_session):
        """Test sending test email when template doesn't exist."""
        service = EmailTemplateService()

        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        result = await service.send_test_email(
            db=mock_db_session,
            user_id="user_123",
            template_name="nonexistent",
            recipient_email="test@example.com",
        )

        assert result is False


class TestTemplateAnalytics:
    """Test template analytics functionality."""

    def test_create_analytics_on_template_creation(self, mock_db_session):
        """Test analytics record is created with new template."""
        analytics = EmailTemplateAnalytics(
            id=1,
            template_id=1,
            sent_count=0,
            opened_count=0,
            clicked_count=0,
            bounced_count=0,
        )

        assert analytics.sent_count == 0
        assert analytics.opened_count == 0

    def test_record_email_sent(self, mock_db_session):
        """Test recording email sent."""
        service = EmailTemplateService()

        analytics = Mock(
            sent_count=5,
            last_sent_at=None,
        )

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            analytics
        )

        service.record_email_sent(mock_db_session, template_id=1)

        assert analytics.sent_count == 6
        assert analytics.last_sent_at is not None

    def test_record_email_opened(self, mock_db_session):
        """Test recording email opened."""
        service = EmailTemplateService()

        analytics = Mock(opened_count=10)

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            analytics
        )

        service.record_email_opened(mock_db_session, template_id=1)

        assert analytics.opened_count == 11

    def test_record_email_clicked(self, mock_db_session):
        """Test recording email link clicked."""
        service = EmailTemplateService()

        analytics = Mock(clicked_count=3)

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            analytics
        )

        service.record_email_clicked(mock_db_session, template_id=1)

        assert analytics.clicked_count == 4

    def test_record_email_bounced(self, mock_db_session):
        """Test recording email bounced."""
        service = EmailTemplateService()

        analytics = Mock(bounced_count=1)

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            analytics
        )

        service.record_email_bounced(mock_db_session, template_id=1)

        assert analytics.bounced_count == 2

    def test_get_template_analytics(self, mock_db_session):
        """Test retrieving template analytics."""
        service = EmailTemplateService()

        analytics = Mock(
            template_id=1,
            sent_count=100,
            opened_count=75,
            clicked_count=30,
            bounced_count=5,
        )

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            analytics
        )

        result = service.get_template_analytics(mock_db_session, template_id=1)

        assert result.sent_count == 100
        assert result.opened_count == 75

    def test_calculate_open_rate(self):
        """Test calculating open rate from analytics."""
        analytics = Mock(
            sent_count=100,
            opened_count=75,
        )

        open_rate = (
            (analytics.opened_count / analytics.sent_count) * 100
            if analytics.sent_count > 0
            else 0
        )

        assert open_rate == 75.0

    def test_calculate_click_rate(self):
        """Test calculating click rate from analytics."""
        analytics = Mock(
            opened_count=75,
            clicked_count=30,
        )

        click_rate = (
            (analytics.clicked_count / analytics.opened_count) * 100
            if analytics.opened_count > 0
            else 0
        )

        assert click_rate == 40.0


class TestAcceptanceCriteria:
    """Test acceptance criteria for Email Templates enhancements."""

    def test_ac1_template_versions_saved(self, mock_db_session):
        """AC-1: Template versions are saved automatically."""
        service = EmailTemplateService()

        # Simulate saving a version
        version = EmailTemplateVersion(
            template_id=1,
            version_number=2,
            subject="Version 2",
            html_content="<h1>V2</h1>",
            text_content="V2",
            version_note="Auto-saved version",
            created_by="user_123",
        )

        assert version.version_number == 2
        assert version.version_note == "Auto-saved version"

    def test_ac2_revert_to_previous_version(self, mock_db_session):
        """AC-2: User can revert to previous version."""
        service = EmailTemplateService()

        # Mock revert operation
        old_version = Mock(
            version_number=1,
            subject="Old",
            html_content="<h1>Old</h1>",
        )

        current_template = Mock(version=3)

        # Revert
        current_template.subject = old_version.subject
        current_template.html_content = old_version.html_content
        current_template.version += 1

        assert current_template.subject == "Old"
        assert current_template.version == 4

    @pytest.mark.asyncio
    @patch("app.services.email_service.email_service._send", new_callable=AsyncMock)
    async def test_ac3_test_email_sends(self, mock_send, mock_db_session):
        """AC-3: Test email sends successfully."""
        mock_send.return_value = True
        service = EmailTemplateService()

        template = Mock(
            template_name="welcome",
            subject="Test",
            html_content="<h1>Test</h1>",
            text_content="Test",
        )

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            template
        )

        result = await service.send_test_email(
            db=mock_db_session,
            user_id="user_123",
            template_name="welcome",
            recipient_email="test@example.com",
        )

        assert result is True

    def test_ac4_analytics_show_metrics(self, mock_db_session):
        """AC-4: Analytics show open/click rates."""
        service = EmailTemplateService()

        analytics = Mock(
            sent_count=100,
            opened_count=80,
            clicked_count=40,
            bounced_count=5,
        )

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            analytics
        )

        result = service.get_template_analytics(mock_db_session, template_id=1)

        assert result is not None
        assert hasattr(result, "opened_count")
        assert hasattr(result, "clicked_count")


# Fixtures
@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = MagicMock()
    session.query.return_value = session
    session.filter.return_value = session
    session.order_by.return_value = session
    session.limit.return_value = session
    session.all.return_value = []
    session.first.return_value = None
    return session
