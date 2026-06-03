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

        # Base template generator for consistent layout
        def _wrap_body(body_html: str, title: str) -> str:
            return f"""<html>
<body style="margin:0;padding:0;background:#f4f4f5;font-family:'Outfit',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:40px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
      <tr>
        <td style="background:linear-gradient(135deg,#FE3C72,#E0245E);padding:32px 40px;text-align:center;">
          <h1 style="margin:0;color:#ffffff;font-size:28px;font-weight:800;letter-spacing:-0.5px;">{{{{ company_name }}}}</h1>
          <p style="margin:4px 0 0;color:rgba(255,255,255,0.85);font-size:14px;">{title}</p>
        </td>
      </tr>
      <tr>
        <td style="padding:40px;">
          {body_html}
        </td>
      </tr>
      <tr>
        <td style="background:#f9fafb;padding:24px 40px;border-top:1px solid #e5e7eb;text-align:center;">
          <p style="margin:0;color:#9ca3af;font-size:12px;">
            &copy; 2026 {{{{ company_name }}}} &middot; Support: {{{{ support_email }}}}
          </p>
        </td>
      </tr>
    </table>
  </td></tr>
</table>
</body></html>"""

        defaults = {
            "welcome": {
                "subject": "Welcome to {{ company_name }}!",
                "html": _wrap_body(
                    """
<h2 style="margin:0 0 16px;color:#111827;font-size:22px;font-weight:700;">Welcome {{ user_name }}!</h2>
<p style="margin:0 0 24px;color:#6b7280;font-size:15px;line-height:1.6;">
  Thank you for joining {{ company_name }}. We're excited to have you on board and can't wait to help you get started.
</p>
<table cellpadding="0" cellspacing="0" style="margin:0 0 32px;">
  <tr>
    <td style="background:linear-gradient(135deg,#FE3C72,#E0245E);border-radius:8px;">
      <a href="https://vrenum.app/dashboard" style="display:inline-block;padding:14px 32px;color:#ffffff;font-size:16px;font-weight:700;text-decoration:none;">Go to Dashboard &rarr;</a>
    </td>
  </tr>
</table>
<p style="margin:0;color:#9ca3af;font-size:13px;">
  If you have any questions, reach out to us at {{ support_email }}
</p>
""",
                    "Welcome Aboard",
                ),
            },
            "verification_code": {
                "subject": "Your verification code for {{ service_name }}",
                "html": _wrap_body(
                    """
<h2 style="margin:0 0 16px;color:#111827;font-size:22px;font-weight:700;">Verification Code</h2>
<p style="margin:0 0 24px;color:#6b7280;font-size:15px;line-height:1.6;">
  Hi {{ user_name }}, your verification code for <strong>{{ service_name }}</strong> on phone number {{ phone_number }} is:
</p>
<div style="background:#f4f4f5;border-radius:8px;padding:20px;text-align:center;margin-bottom:24px;">
  <span style="font-family:monospace;font-size:40px;letter-spacing:5px;font-weight:800;color:#111827;">{{ verification_code }}</span>
</div>
<div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:16px 20px;">
  <p style="margin:0;color:#92400e;font-size:13px;line-height:1.5;">
    ⏱ This code expires in <strong>{{ expires_in }} minutes</strong>. Do not share this code with anyone.
  </p>
</div>
""",
                    "Security Verification",
                ),
            },
            "payment_success": {
                "subject": "Payment successful - {{ amount }} {{ currency }}",
                "html": _wrap_body(
                    """
<h2 style="margin:0 0 16px;color:#111827;font-size:22px;font-weight:700;">✅ Payment Successful</h2>
<p style="margin:0 0 24px;color:#6b7280;font-size:15px;">Hi {{ user_name }}, your payment has been processed successfully.</p>
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;border-radius:12px;overflow:hidden;margin-bottom:24px;">
  <tr style="border-bottom:1px solid #e5e7eb;">
    <td style="padding:14px 20px;color:#6b7280;font-size:14px;">Amount Paid</td>
    <td style="padding:14px 20px;color:#111827;font-size:14px;font-weight:600;text-align:right;">{{ amount }} {{ currency }}</td>
  </tr>
  <tr style="border-bottom:1px solid #e5e7eb;">
    <td style="padding:14px 20px;color:#6b7280;font-size:14px;">Credits Added</td>
    <td style="padding:14px 20px;color:#10b981;font-size:14px;font-weight:700;text-align:right;">+{{ credits_added }}</td>
  </tr>
  <tr style="border-bottom:1px solid #e5e7eb;">
    <td style="padding:14px 20px;color:#6b7280;font-size:14px;">New Balance</td>
    <td style="padding:14px 20px;color:#FE3C72;font-size:16px;font-weight:800;text-align:right;">{{ new_balance }} {{ currency }}</td>
  </tr>
  <tr>
    <td style="padding:14px 20px;color:#6b7280;font-size:14px;">Transaction ID</td>
    <td style="padding:14px 20px;color:#111827;font-size:14px;text-align:right;">{{ transaction_id }}</td>
  </tr>
</table>
""",
                    "Payment Receipt",
                ),
            },
            "payment_failed": {
                "subject": "Payment failed - {{ amount }} {{ currency }}",
                "html": _wrap_body(
                    """
<h2 style="margin:0 0 16px;color:#ef4444;font-size:22px;font-weight:700;">❌ Payment Failed</h2>
<p style="margin:0 0 24px;color:#6b7280;font-size:15px;">Hi {{ user_name }}, your payment of {{ amount }} {{ currency }} failed to process.</p>
<table width="100%" cellpadding="0" cellspacing="0" style="background:#fef2f2;border-radius:12px;overflow:hidden;margin-bottom:24px;">
  <tr>
    <td style="padding:14px 20px;color:#6b7280;font-size:14px;">Reason for Failure</td>
    <td style="padding:14px 20px;color:#ef4444;font-size:14px;font-weight:600;text-align:right;">{{ reason }}</td>
  </tr>
</table>
<p style="margin:0;color:#9ca3af;font-size:13px;">
  Please try again or contact {{ support_email }} for assistance.
</p>
""",
                    "Payment Failed Alert",
                ),
            },
            "low_balance": {
                "subject": "Low balance alert",
                "html": _wrap_body(
                    """
<h2 style="margin:0 0 16px;color:#111827;font-size:22px;font-weight:700;">⚠️ Low Balance Alert</h2>
<p style="margin:0 0 24px;color:#6b7280;font-size:15px;line-height:1.6;">
  Hi {{ user_name }}, your account balance is running low: <strong>{{ current_balance }} {{ currency }}</strong>.
</p>
<table cellpadding="0" cellspacing="0" style="margin:0 0 24px;">
  <tr>
    <td style="background:linear-gradient(135deg,#FE3C72,#E0245E);border-radius:8px;">
      <a href="{{ top_up_url }}" style="display:inline-block;padding:14px 32px;color:#ffffff;font-size:16px;font-weight:700;text-decoration:none;">Top up now &rarr;</a>
    </td>
  </tr>
</table>
""",
                    "Low Balance Warning",
                ),
            },
            "tier_upgrade": {
                "subject": "Tier upgraded to {{ new_tier }}",
                "html": _wrap_body(
                    """
<h2 style="margin:0 0 16px;color:#111827;font-size:22px;font-weight:700;">⭐ Plan Upgraded!</h2>
<p style="margin:0 0 24px;color:#6b7280;font-size:15px;line-height:1.6;">
  Hi {{ user_name }}, your subscription tier has been upgraded from <strong>{{ old_tier }}</strong> to <strong>{{ new_tier }}</strong>.
</p>
<div style="background:#f0fdf4;border-radius:12px;padding:20px;margin-bottom:24px;">
  <p style="margin:0 0 12px;font-weight:700;color:#111827;">New features unlocked:</p>
  <p style="margin:0;color:#166534;font-size:14px;">{{ new_features }}</p>
</div>
<p style="margin:0;color:#9ca3af;font-size:13px;">Effective Date: {{ effective_date }}</p>
""",
                    "Subscription Upgrade",
                ),
            },
            "password_reset": {
                "subject": "Password reset request",
                "html": _wrap_body(
                    """
<h2 style="margin:0 0 16px;color:#111827;font-size:22px;font-weight:700;">Password Reset</h2>
<p style="margin:0 0 24px;color:#6b7280;font-size:15px;line-height:1.6;">
  Hi {{ user_name }}, we received a request to reset your password. Click the link below to reset it:
</p>
<table cellpadding="0" cellspacing="0" style="margin:0 0 24px;">
  <tr>
    <td style="background:linear-gradient(135deg,#FE3C72,#E0245E);border-radius:8px;">
      <a href="{{ reset_link }}" style="display:inline-block;padding:14px 32px;color:#ffffff;font-size:16px;font-weight:700;text-decoration:none;">Reset Password &rarr;</a>
    </td>
  </tr>
</table>
<div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:16px 20px;">
  <p style="margin:0;color:#92400e;font-size:13px;line-height:1.5;">
    ⏱ This link expires in <strong>{{ expires_in }} minutes</strong>. If you didn't request a password reset, you can safely ignore this email.
  </p>
</div>
""",
                    "Account Security",
                ),
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
                "company_name": "VRENUM SMS",
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
