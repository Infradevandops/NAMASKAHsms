"""Tests for email template enhancements (versioning, test email, analytics)"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from app.services.email_template_service import EmailTemplateService


class TestEmailTemplateVersioning:
    """Test email template versioning functionality"""

    def test_create_template_creates_initial_version(self, db_session, test_user):
        """Test that creating a template initializes version 1"""
        service = EmailTemplateService()

        template = service.create_or_update_template(
            db=db_session,
            user_id=test_user.id,
            template_name="welcome",
            subject="Welcome {{ user_name }}!",
            html_content="<h1>Welcome {{ user_name }}</h1>",
            version_note="Initial version",
        )

        assert template.version == 1
        assert template.subject == "Welcome {{ user_name }}!"

    def test_update_template_increments_version(self, db_session, test_user):
        """Test that updating a template increments version number"""
        service = EmailTemplateService()

        # Create initial template
        template = service.create_or_update_template(
            db=db_session,
            user_id=test_user.id,
            template_name="welcome",
            subject="Welcome!",
            html_content="<h1>Welcome</h1>",
        )
        initial_version = template.version

        # Update template
        updated = service.create_or_update_template(
            db=db_session,
            user_id=test_user.id,
            template_name="welcome",
            subject="Welcome Updated!",
            html_content="<h1>Welcome Updated</h1>",
            version_note="Updated subject",
        )

        assert updated.version == initial_version + 1
        assert updated.subject == "Welcome Updated!"

    def test_get_template_versions_returns_history(self, db_session, test_user):
        """Test retrieving version history"""
        service = EmailTemplateService()

        # Create and update template multiple times
        template = service.create_or_update_template(
            db=db_session,
            user_id=test_user.id,
            template_name="welcome",
            subject="V1",
            html_content="<h1>V1</h1>",
        )

        for i in range(2, 5):
            service.create_or_update_template(
                db=db_session,
                user_id=test_user.id,
                template_name="welcome",
                subject=f"V{i}",
                html_content=f"<h1>V{i}</h1>",
                version_note=f"Version {i}",
            )

        versions = service.get_template_versions(db_session, template.id)

        assert len(versions) >= 3
        assert (
            versions[0].version_number > versions[-1].version_number
        )  # Descending order

    def test_revert_to_version_restores_content(self, db_session, test_user):
        """Test reverting to a previous version"""
        service = EmailTemplateService()

        # Create template
        template = service.create_or_update_template(
            db=db_session,
            user_id=test_user.id,
            template_name="welcome",
            subject="Original",
            html_content="<h1>Original</h1>",
        )

        # Update to V2
        service.create_or_update_template(
            db=db_session,
            user_id=test_user.id,
            template_name="welcome",
            subject="Updated",
            html_content="<h1>Updated</h1>",
        )

        # Revert to V1
        reverted = service.revert_to_version(
            db=db_session,
            template_id=template.id,
            version_number=1,
            user_id=test_user.id,
        )

        assert reverted.subject == "Original"
        assert reverted.html_content == "<h1>Original</h1>"
        assert reverted.version == 3  # New version created

    def test_revert_to_nonexistent_version_raises_error(self, db_session, test_user):
        """Test reverting to non-existent version raises error"""
        service = EmailTemplateService()

        template = service.create_or_update_template(
            db=db_session,
            user_id=test_user.id,
            template_name="welcome",
            subject="Test",
            html_content="<h1>Test</h1>",
        )

        with pytest.raises(ValueError, match="Version .* not found"):
            service.revert_to_version(
                db=db_session,
                template_id=template.id,
                version_number=999,
                user_id=test_user.id,
            )


class TestEmailTemplateTestEmail:
    """Test email template test email functionality"""

    @pytest.mark.asyncio
    async def test_send_test_email_success(self, db_session, test_user):
        """Test sending test email successfully"""
        service = EmailTemplateService()

        # Create template
        service.create_or_update_template(
            db=db_session,
            user_id=test_user.id,
            template_name="welcome",
            subject="Welcome {{ user_name }}!",
            html_content="<h1>Welcome {{ user_name }}</h1>",
        )

        # Send test email
        success = await service.send_test_email(
            db=db_session,
            user_id=test_user.id,
            template_name="welcome",
            recipient_email="test@example.com",
        )

        assert success is True

    @pytest.mark.asyncio
    async def test_send_test_email_nonexistent_template(self, db_session, test_user):
        """Test sending test email for non-existent template fails"""
        service = EmailTemplateService()

        success = await service.send_test_email(
            db=db_session,
            user_id=test_user.id,
            template_name="nonexistent",
            recipient_email="test@example.com",
        )

        assert success is False

    @pytest.mark.asyncio
    async def test_send_test_email_uses_test_variables(self, db_session, test_user):
        """Test that test email uses appropriate test variables"""
        service = EmailTemplateService()

        service.create_or_update_template(
            db=db_session,
            user_id=test_user.id,
            template_name="verification_code",
            subject="Code: {{ verification_code }}",
            html_content="<h1>{{ verification_code }}</h1>",
        )

        test_vars = service._get_test_variables("verification_code")

        assert "verification_code" in test_vars
        assert "phone_number" in test_vars
        assert "service_name" in test_vars


class TestEmailTemplateAnalytics:
    """Test email template analytics functionality"""

    def test_get_template_analytics_returns_stats(self, db_session, test_user):
        """Test retrieving template analytics"""
        service = EmailTemplateService()

        template = service.create_or_update_template(
            db=db_session,
            user_id=test_user.id,
            template_name="welcome",
            subject="Welcome!",
            html_content="<h1>Welcome</h1>",
        )

        analytics = service.get_template_analytics(db_session, template.id)

        assert analytics is not None
        assert analytics.sent_count == 0
        assert analytics.opened_count == 0
        assert analytics.clicked_count == 0
        assert analytics.bounced_count == 0

    def test_record_email_sent_increments_count(self, db_session, test_user):
        """Test recording sent email increments counter"""
        service = EmailTemplateService()

        template = service.create_or_update_template(
            db=db_session,
            user_id=test_user.id,
            template_name="welcome",
            subject="Welcome!",
            html_content="<h1>Welcome</h1>",
        )

        # Record sent
        service.record_email_sent(db_session, template.id)

        analytics = service.get_template_analytics(db_session, template.id)
        assert analytics.sent_count == 1
        assert analytics.last_sent_at is not None

    def test_record_email_opened_increments_count(self, db_session, test_user):
        """Test recording opened email increments counter"""
        service = EmailTemplateService()

        template = service.create_or_update_template(
            db=db_session,
            user_id=test_user.id,
            template_name="welcome",
            subject="Welcome!",
            html_content="<h1>Welcome</h1>",
        )

        service.record_email_opened(db_session, template.id)

        analytics = service.get_template_analytics(db_session, template.id)
        assert analytics.opened_count == 1

    def test_record_email_clicked_increments_count(self, db_session, test_user):
        """Test recording clicked email increments counter"""
        service = EmailTemplateService()

        template = service.create_or_update_template(
            db=db_session,
            user_id=test_user.id,
            template_name="welcome",
            subject="Welcome!",
            html_content="<h1>Welcome</h1>",
        )

        service.record_email_clicked(db_session, template.id)

        analytics = service.get_template_analytics(db_session, template.id)
        assert analytics.clicked_count == 1

    def test_record_email_bounced_increments_count(self, db_session, test_user):
        """Test recording bounced email increments counter"""
        service = EmailTemplateService()

        template = service.create_or_update_template(
            db=db_session,
            user_id=test_user.id,
            template_name="welcome",
            subject="Welcome!",
            html_content="<h1>Welcome</h1>",
        )

        service.record_email_bounced(db_session, template.id)

        analytics = service.get_template_analytics(db_session, template.id)
        assert analytics.bounced_count == 1


class TestAcceptanceCriteria:
    """Test acceptance criteria for email template enhancements"""

    def test_ac1_users_can_save_template_versions(self, db_session, test_user):
        """AC-1: Users can save template versions"""
        service = EmailTemplateService()

        # Create initial version
        template = service.create_or_update_template(
            db=db_session,
            user_id=test_user.id,
            template_name="welcome",
            subject="V1",
            html_content="<h1>V1</h1>",
            version_note="Initial version",
        )

        # Update creates new version
        updated = service.create_or_update_template(
            db=db_session,
            user_id=test_user.id,
            template_name="welcome",
            subject="V2",
            html_content="<h1>V2</h1>",
            version_note="Second version",
        )

        assert updated.version == 2
        versions = service.get_template_versions(db_session, template.id)
        assert len(versions) >= 1

    def test_ac2_users_can_rollback_to_previous_versions(self, db_session, test_user):
        """AC-2: Users can rollback to previous versions"""
        service = EmailTemplateService()

        template = service.create_or_update_template(
            db=db_session,
            user_id=test_user.id,
            template_name="welcome",
            subject="Original",
            html_content="<h1>Original</h1>",
        )

        service.create_or_update_template(
            db=db_session,
            user_id=test_user.id,
            template_name="welcome",
            subject="Modified",
            html_content="<h1>Modified</h1>",
        )

        reverted = service.revert_to_version(
            db=db_session,
            template_id=template.id,
            version_number=1,
            user_id=test_user.id,
        )

        assert reverted.subject == "Original"

    @pytest.mark.asyncio
    async def test_ac3_users_can_send_test_emails(self, db_session, test_user):
        """AC-3: Users can send test emails"""
        service = EmailTemplateService()

        service.create_or_update_template(
            db=db_session,
            user_id=test_user.id,
            template_name="welcome",
            subject="Test",
            html_content="<h1>Test</h1>",
        )

        success = await service.send_test_email(
            db=db_session,
            user_id=test_user.id,
            template_name="welcome",
            recipient_email="test@example.com",
        )

        assert success is True

    def test_ac4_analytics_show_open_click_rates(self, db_session, test_user):
        """AC-4: Analytics show open/click rates"""
        service = EmailTemplateService()

        template = service.create_or_update_template(
            db=db_session,
            user_id=test_user.id,
            template_name="welcome",
            subject="Test",
            html_content="<h1>Test</h1>",
        )

        # Simulate email activity
        for _ in range(10):
            service.record_email_sent(db_session, template.id)
        for _ in range(7):
            service.record_email_opened(db_session, template.id)
        for _ in range(3):
            service.record_email_clicked(db_session, template.id)

        analytics = service.get_template_analytics(db_session, template.id)

        assert analytics.sent_count == 10
        assert analytics.opened_count == 7
        assert analytics.clicked_count == 3

        # Calculate rates
        open_rate = (analytics.opened_count / analytics.sent_count) * 100
        click_rate = (analytics.clicked_count / analytics.sent_count) * 100

        assert open_rate == 70.0
        assert click_rate == 30.0
