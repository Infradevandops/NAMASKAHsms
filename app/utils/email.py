"""Email utilities for SMTP configuration and template management."""


import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template
from typing import Any, Dict, Optional
from app.core.config import settings
import re

logger = logging.getLogger(__name__)


class EmailTemplate:

    """Simple email template class."""

    def __init__(self, subject: str, html_body: str, text_body: Optional[str] = None):

        self.subject = subject
        self.html_body = html_body
        self.text_body = text_body or self._html_to_text(html_body)

        @staticmethod
    def _html_to_text(html: str) -> str:

        """Convert HTML to plain text (basic implementation)."""

        # Remove HTML tags
        text = re.sub("<[^<]+?>", "", html)
        # Clean up whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def render(self, **kwargs) -> Dict[str, str]:

        """Render template with variables."""
        subject = Template(self.subject).safe_substitute(**kwargs)
        html_body = Template(self.html_body).safe_substitute(**kwargs)
        text_body = Template(self.text_body).safe_substitute(**kwargs)

        return {"subject": subject, "html_body": html_body, "text_body": text_body}


class EmailService:

        """Simple email service for SMTP operations."""

    def __init__(self):

        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_email = settings.from_email

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = True,
        from_email: Optional[str] = None,
        ) -> bool:
        """Send email via SMTP."""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_email or self.from_email
            msg["To"] = to_email

            # Add body
        if is_html:
                msg.attach(MIMEText(body, "html"))
        else:
                msg.attach(MIMEText(body, "plain"))

            # Send email
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
        if self.smtp_user and self.smtp_password:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)

                server.send_message(msg)

            logger.info("Email sent successfully to %s", to_email)
        return True

        except Exception as e:
            logger.error("Failed to send email to %s: %s", to_email, str(e))
        return False

    async def send_template_email(
        self,
        to_email: str,
        template: EmailTemplate,
        template_vars: Optional[Dict[str, Any]] = None,
        ) -> bool:
        """Send email using template."""
        template_vars = template_vars or {}
        rendered = template.render(**template_vars)

        return await self.send_email(
            to_email=to_email,
            subject=rendered["subject"],
            body=rendered["html_body"],
            is_html=True,
        )


# Pre - defined email templates
        WELCOME_TEMPLATE = EmailTemplate(
        subject="Welcome to Namaskah SMS - $name",
        html_body="""
        <h2>Welcome to Namaskah SMS!</h2>
        <p>Hi $name,</p>
        <p>Thank you for joining Namaskah SMS. Your account has been created successfully.</p>
        <p><strong>Account Details:</strong></p>
        <ul>
        <li>Email: $email</li>
        <li>Credits: $credits NGN</li>
        </ul>
        <p>You can now start using our SMS verification services.</p>
        <p>Best regards,<br>Namaskah Team</p>
        """,
        )

        VERIFICATION_COMPLETE_TEMPLATE = EmailTemplate(
        subject="Verification Completed - $service_name",
        html_body="""
        <h2>Verification Completed</h2>
        <p>Hi $name,</p>
        <p>Your $service_name verification has been completed successfully!</p>
        <p><strong>Details:</strong></p>
        <ul>
        <li>Service: $service_name</li>
        <li>Phone Number: $phone_number</li>
        <li>Cost: $cost NGN</li>
        <li>Completed At: $completed_at</li>
        </ul>
        <p>Thank you for using Namaskah SMS.</p>
        <p>Best regards,<br>Namaskah Team</p>
        """,
        )

        PASSWORD_RESET_TEMPLATE = EmailTemplate(
        subject="Password Reset - Namaskah SMS",
        html_body="""
        <h2>Password Reset Request</h2>
        <p>Hi $name,</p>
        <p>You requested a password reset for your Namaskah SMS account.</p>
        <p>Your reset code is: <strong>$reset_code</strong></p>
        <p>This code will expire in 15 minutes.</p>
        <p>If you didn't request this reset, please ignore this email.</p>
        <p>Best regards,<br>Namaskah Team</p>
        """,
        )

        RECEIPT_TEMPLATE = EmailTemplate(
        subject="Payment Receipt - Namaskah SMS",
        html_body="""
        <h2>Payment Receipt</h2>
        <p>Hi $name,</p>
        <p>Thank you for your payment. Here are the details:</p>
        <p><strong>Transaction Details:</strong></p>
        <ul>
        <li>Amount: $amount NGN</li>
        <li>Transaction ID: $transaction_id</li>
        <li>Date: $date</li>
        <li>Payment Method: $payment_method</li>
        </ul>
        <p>Your account has been credited with $credits_added NGN.</p>
        <p>Best regards,<br>Namaskah Team</p>
        """,
        )


    def get_email_service() -> EmailService:

        """Get email service instance."""
        return EmailService()