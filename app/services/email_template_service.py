"""Email template service for whitelabel custom emails"""

import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from jinja2 import Template
from sqlalchemy.orm import Session

from app.models.whitelabel_models import (
    EmailTemplateAnalytics,
    EmailTemplateVersion,
    WhitelabelEmailTemplate,
)

logger = logging.getLogger(__name__)


class EmailTemplateService:
    """Service for managing and rendering email templates"""

    # Available template types
    TEMPLATE_TYPES = [
        "welcome",
        "verification_code",
        "payment_success",
        "payment_failed",
        "low_balance",
        "tier_upgrade",
        "password_reset",
    ]

    # Available variables per template type
    TEMPLATE_VARIABLES = {
        "welcome": ["user_name", "user_email", "company_name", "support_email"],
        "verification_code": [
            "user_name",
            "verification_code",
            "phone_number",
            "service_name",
            "expires_in",
        ],
        "payment_success": [
            "user_name",
            "amount",
            "currency",
            "credits_added",
            "new_balance",
            "transaction_id",
        ],
        "payment_failed": [
            "user_name",
            "amount",
            "currency",
            "reason",
            "support_email",
        ],
        "low_balance": ["user_name", "current_balance", "currency", "top_up_url"],
        "tier_upgrade": [
            "user_name",
            "old_tier",
            "new_tier",
            "new_features",
            "effective_date",
        ],
        "password_reset": ["user_name", "reset_link", "expires_in"],
    }

    def get_template(
        self, db: Session, user_id: int, template_name: str
    ) -> Optional[WhitelabelEmailTemplate]:
        """Get email template by name"""
        return (
            db.query(WhitelabelEmailTemplate)
            .filter(
                WhitelabelEmailTemplate.user_id == user_id,
                WhitelabelEmailTemplate.template_name == template_name,
                WhitelabelEmailTemplate.active == True,
            )
            .first()
        )

    def create_or_update_template(
        self,
        db: Session,
        user_id: int,
        template_name: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        version_note: Optional[str] = None,
    ) -> WhitelabelEmailTemplate:
        """Create or update email template with versioning"""
        if template_name not in self.TEMPLATE_TYPES:
            raise ValueError(f"Invalid template type: {template_name}")

        # Validate variables in template
        self._validate_template_variables(template_name, html_content)

        template = self.get_template(db, user_id, template_name)

        if template:
            # Save current version to history
            version = EmailTemplateVersion(
                template_id=template.id,
                version_number=template.version,
                subject=template.subject,
                html_content=template.html_content,
                text_content=template.text_content,
                version_note=version_note or "Auto-saved version",
                created_by=str(user_id),
            )
            db.add(version)

            # Update template
            template.subject = subject
            template.html_content = html_content
            template.text_content = text_content or self._html_to_text(html_content)
            template.version += 1
        else:
            template = WhitelabelEmailTemplate(
                user_id=user_id,
                template_name=template_name,
                subject=subject,
                html_content=html_content,
                text_content=text_content or self._html_to_text(html_content),
                active=True,
                version=1,
            )
            db.add(template)
            db.flush()  # Get template.id

            # Create initial analytics record
            analytics = EmailTemplateAnalytics(template_id=template.id)
            db.add(analytics)

        db.commit()
        db.refresh(template)
        return template

    def render_template(
        self,
        db: Session,
        user_id: int,
        template_name: str,
        variables: Dict[str, str],
    ) -> tuple[str, str, str]:
        """
        Render email template with variables

        Returns:
            Tuple of (subject, html_content, text_content)
        """
        template = self.get_template(db, user_id, template_name)

        if not template:
            raise ValueError(f"Template not found: {template_name}")

        # Render subject
        subject = Template(template.subject).render(**variables)

        # Render HTML content
        html_content = Template(template.html_content).render(**variables)

        # Render text content
        text_content = Template(template.text_content).render(**variables)

        return subject, html_content, text_content

    def _validate_template_variables(self, template_name: str, content: str) -> None:
        """Validate that template only uses allowed variables"""
        allowed_vars = self.TEMPLATE_VARIABLES.get(template_name, [])

        # Extract variables from template ({{ variable_name }})
        pattern = r"\{\{\s*(\w+)\s*\}\}"
        used_vars = set(re.findall(pattern, content))

        # Check for invalid variables
        invalid_vars = used_vars - set(allowed_vars)
        if invalid_vars:
            raise ValueError(
                f"Invalid variables in template: {', '.join(invalid_vars)}. "
                f"Allowed: {', '.join(allowed_vars)}"
            )

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text (basic implementation)"""
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", html)
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def get_default_template(self, template_name: str) -> Dict[str, str]:
        """Get default template content"""
        defaults = {
            "welcome": {
                "subject": "Welcome to {{ company_name }}!",
                "html": """
<h1>Welcome {{ user_name }}!</h1>
<p>Thank you for joining {{ company_name }}. We're excited to have you on board.</p>
<p>If you have any questions, contact us at {{ support_email }}</p>
""",
            },
            "verification_code": {
                "subject": "Your verification code for {{ service_name }}",
                "html": """
<h1>Verification Code</h1>
<p>Hi {{ user_name }},</p>
<p>Your verification code for {{ service_name }} ({{ phone_number }}) is:</p>
<h2 style="font-size: 32px; letter-spacing: 5px;">{{ verification_code }}</h2>
<p>This code expires in {{ expires_in }} minutes.</p>
""",
            },
            "payment_success": {
                "subject": "Payment successful - {{ amount }} {{ currency }}",
                "html": """
<h1>Payment Successful</h1>
<p>Hi {{ user_name }},</p>
<p>Your payment of {{ amount }} {{ currency }} was successful.</p>
<p>Credits added: {{ credits_added }}</p>
<p>New balance: {{ new_balance }} {{ currency }}</p>
<p>Transaction ID: {{ transaction_id }}</p>
""",
            },
            "payment_failed": {
                "subject": "Payment failed - {{ amount }} {{ currency }}",
                "html": """
<h1>Payment Failed</h1>
<p>Hi {{ user_name }},</p>
<p>Your payment of {{ amount }} {{ currency }} failed.</p>
<p>Reason: {{ reason }}</p>
<p>Please try again or contact {{ support_email }} for assistance.</p>
""",
            },
            "low_balance": {
                "subject": "Low balance alert",
                "html": """
<h1>Low Balance Alert</h1>
<p>Hi {{ user_name }},</p>
<p>Your account balance is low: {{ current_balance }} {{ currency }}</p>
<p><a href="{{ top_up_url }}">Top up now</a> to continue using our services.</p>
""",
            },
            "tier_upgrade": {
                "subject": "Tier upgraded to {{ new_tier }}",
                "html": """
<h1>Tier Upgraded!</h1>
<p>Hi {{ user_name }},</p>
<p>Your tier has been upgraded from {{ old_tier }} to {{ new_tier }}.</p>
<p>New features: {{ new_features }}</p>
<p>Effective date: {{ effective_date }}</p>
""",
            },
            "password_reset": {
                "subject": "Password reset request",
                "html": """
<h1>Password Reset</h1>
<p>Hi {{ user_name }},</p>
<p>Click the link below to reset your password:</p>
<p><a href="{{ reset_link }}">Reset Password</a></p>
<p>This link expires in {{ expires_in }} minutes.</p>
""",
            },
        }

        return defaults.get(template_name, {"subject": "", "html": ""})

    def get_template_versions(
        self, db: Session, template_id: int, limit: int = 10
    ) -> List[EmailTemplateVersion]:
        """Get version history for a template"""
        return (
            db.query(EmailTemplateVersion)
            .filter(EmailTemplateVersion.template_id == template_id)
            .order_by(EmailTemplateVersion.version_number.desc())
            .limit(limit)
            .all()
        )

    def revert_to_version(
        self, db: Session, template_id: int, version_number: int, user_id: int
    ) -> WhitelabelEmailTemplate:
        """Revert template to a previous version"""
        # Get the version
        version = (
            db.query(EmailTemplateVersion)
            .filter(
                EmailTemplateVersion.template_id == template_id,
                EmailTemplateVersion.version_number == version_number,
            )
            .first()
        )

        if not version:
            raise ValueError(f"Version {version_number} not found")

        # Get current template
        template = (
            db.query(WhitelabelEmailTemplate)
            .filter(WhitelabelEmailTemplate.id == template_id)
            .first()
        )

        if not template:
            raise ValueError("Template not found")

        # Save current as version before reverting
        current_version = EmailTemplateVersion(
            template_id=template.id,
            version_number=template.version,
            subject=template.subject,
            html_content=template.html_content,
            text_content=template.text_content,
            version_note=f"Before reverting to v{version_number}",
            created_by=str(user_id),
        )
        db.add(current_version)

        # Revert to old version
        template.subject = version.subject
        template.html_content = version.html_content
        template.text_content = version.text_content
        template.version += 1

        db.commit()
        db.refresh(template)
        return template

    async def send_test_email(
        self,
        db: Session,
        user_id: int,
        template_name: str,
        recipient_email: str,
        test_variables: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Send a test email with sample data"""
        try:
            # Get template
            template = self.get_template(db, user_id, template_name)
            if not template:
                raise ValueError(f"Template not found: {template_name}")

            # Use test variables or defaults
            if not test_variables:
                test_variables = self._get_test_variables(template_name)

            # Render template
            subject, html_content, text_content = self.render_template(
                db, user_id, template_name, test_variables
            )

            # Send via email service
            from app.services.email_service import email_service

            return await email_service._send(recipient_email, subject, html_content)
        except Exception as e:
            logger.error(f"Failed to send test email: {e}")
            return False

    def _get_test_variables(self, template_name: str) -> Dict[str, str]:
        """Get test variables for a template"""
        test_data = {
            "welcome": {
                "user_name": "John Doe",
                "user_email": "john@example.com",
                "company_name": "VRENUM ACTV8TN",
                "support_email": "support@vrenum.app",
            },
            "verification_code": {
                "user_name": "John Doe",
                "verification_code": "123456",
                "phone_number": "+1234567890",
                "service_name": "WhatsApp",
                "expires_in": "10",
            },
            "payment_success": {
                "user_name": "John Doe",
                "amount": "10.00",
                "currency": "USD",
                "credits_added": "10.00",
                "new_balance": "25.50",
                "transaction_id": "txn_test123",
            },
            "payment_failed": {
                "user_name": "John Doe",
                "amount": "10.00",
                "currency": "USD",
                "reason": "Insufficient funds",
                "support_email": "support@vrenum.app",
            },
            "low_balance": {
                "user_name": "John Doe",
                "current_balance": "2.50",
                "currency": "USD",
                "top_up_url": "https://vrenum.app/wallet",
            },
            "tier_upgrade": {
                "user_name": "John Doe",
                "old_tier": "Freemium",
                "new_tier": "Pro",
                "new_features": "API Access, Priority Support",
                "effective_date": "2026-05-17",
            },
            "password_reset": {
                "user_name": "John Doe",
                "reset_link": "https://vrenum.app/reset-password?token=test123",
                "expires_in": "30",
            },
        }

        return test_data.get(template_name, {})

    def get_template_analytics(
        self, db: Session, template_id: int
    ) -> Optional[EmailTemplateAnalytics]:
        """Get analytics for a template"""
        return (
            db.query(EmailTemplateAnalytics)
            .filter(EmailTemplateAnalytics.template_id == template_id)
            .first()
        )

    def record_email_sent(self, db: Session, template_id: int) -> None:
        """Record that an email was sent"""
        analytics = self.get_template_analytics(db, template_id)
        if analytics:
            analytics.sent_count += 1
            analytics.last_sent_at = datetime.now(timezone.utc)
            db.commit()

    def record_email_opened(self, db: Session, template_id: int) -> None:
        """Record that an email was opened"""
        analytics = self.get_template_analytics(db, template_id)
        if analytics:
            analytics.opened_count += 1
            db.commit()

    def record_email_clicked(self, db: Session, template_id: int) -> None:
        """Record that a link in email was clicked"""
        analytics = self.get_template_analytics(db, template_id)
        if analytics:
            analytics.clicked_count += 1
            db.commit()

    def record_email_bounced(self, db: Session, template_id: int) -> None:
        """Record that an email bounced"""
        analytics = self.get_template_analytics(db, template_id)
        if analytics:
            analytics.bounced_count += 1
            db.commit()


# Singleton instance
email_template_service = EmailTemplateService()
