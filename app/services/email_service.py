"""Email service for sending payment notifications."""


import asyncio
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailService:

    """Service for sending emails."""

    def __init__(self):

        """Initialize email service with SMTP configuration."""
        settings = get_settings()
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_email = settings.from_email
        self.enabled = bool(self.smtp_host and self.smtp_user and self.smtp_password)

        if self.enabled:
            logger.info("Email service initialized")
        else:
            logger.warning("Email service not configured")

    async def send_payment_receipt(self, user_email: str, payment_details: Dict[str, Any]) -> bool:
        """Send payment receipt email.

        Args:
            user_email: Recipient email address
            payment_details: Payment details dictionary

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Email service not configured, skipping receipt email")
        return False

        try:
            subject = "Payment Receipt - Namaskah SMS"

            # Create HTML email body
            html_body = self._create_receipt_html(payment_details)

            # Send email
            await self._send_email(to_email=user_email, subject=subject, html_body=html_body)

            logger.info(f"Payment receipt sent to {user_email}")
        return True

        except Exception as e:
            logger.error(f"Failed to send payment receipt: {str(e)}")
        return False

    async def send_payment_failed_alert(self, user_email: str, payment_details: Dict[str, Any]) -> bool:
        """Send payment failed alert email.

        Args:
            user_email: Recipient email address
            payment_details: Payment details dictionary

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Email service not configured, skipping failed alert email")
        return False

        try:
            subject = "Payment Failed - Namaskah SMS"

            # Create HTML email body
            html_body = self._create_failed_alert_html(payment_details)

            # Send email
            await self._send_email(to_email=user_email, subject=subject, html_body=html_body)

            logger.info(f"Payment failed alert sent to {user_email}")
        return True

        except Exception as e:
            logger.error(f"Failed to send payment failed alert: {str(e)}")
        return False

    async def send_refund_notification(self, user_email: str, refund_details: Dict[str, Any]) -> bool:
        """Send refund notification email.

        Args:
            user_email: Recipient email address
            refund_details: Refund details dictionary

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Email service not configured, skipping refund email")
        return False

        try:
            subject = "Refund Processed - Namaskah SMS"

            # Create HTML email body
            html_body = self._create_refund_html(refund_details)

            # Send email
            await self._send_email(to_email=user_email, subject=subject, html_body=html_body)

            logger.info(f"Refund notification sent to {user_email}")
        return True

        except Exception as e:
            logger.error(f"Failed to send refund notification: {str(e)}")
        return False

    async def _send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        """Send email via SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email

            # Attach HTML body
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)

            # Send email asynchronously
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_smtp, to_email, message.as_string())

        return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False

    def _send_smtp(self, to_email: str, message: str) -> None:

        """Send email via SMTP (blocking operation).

        Args:
            to_email: Recipient email address
            message: Email message
        """
        try:
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to_email, message)
        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            raise

    def _create_receipt_html(self, payment_details: Dict[str, Any]) -> str:

        """Create HTML for payment receipt email.

        Args:
            payment_details: Payment details dictionary

        Returns:
            HTML email body
        """
        reference = payment_details.get("reference", "N/A")
        amount_usd = payment_details.get("amount_usd", 0)
        credits_added = payment_details.get("credits_added", 0)
        new_balance = payment_details.get("new_balance", 0)
        timestamp = payment_details.get("timestamp", datetime.now(timezone.utc).isoformat())

        return """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #667eea;">Payment Receipt</h2>

                    <p>Thank you for your payment! Your account has been credited successfully.</p>

                    <div style="background: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">Payment Details</h3>

                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>Reference:</strong></td>
                                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{reference}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>Amount Paid:</strong></td>
                                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">${amount_usd:.2f}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>Credits Added:</strong></td>
                                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{credits_added:.2f}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>New Balance:</strong></td>
                                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>{new_balance:.2f}</strong></td>
                            </tr>
                            <tr>
                                <td style="padding: 10px;"><strong>Date:</strong></td>
                                <td style="padding: 10px;">{timestamp}</td>
                            </tr>
                        </table>
                    </div>

                    <p>You can now use your credits to verify phone numbers on Namaskah SMS.</p>

                    <p style="color: #6b7280; font-size: 12px; margin-top: 30px;">
                        If you have any questions, please contact our support team.
                    </p>
                </div>
            </body>
        </html>
        """

    def _create_failed_alert_html(self, payment_details: Dict[str, Any]) -> str:

        """Create HTML for payment failed alert email.

        Args:
            payment_details: Payment details dictionary

        Returns:
            HTML email body
        """
        reference = payment_details.get("reference", "N/A")
        amount_usd = payment_details.get("amount_usd", 0)
        reason = payment_details.get("reason", "Unknown reason")
        timestamp = payment_details.get("timestamp", datetime.now(timezone.utc).isoformat())

        return """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #ef4444;">Payment Failed</h2>

                    <p>Unfortunately, your payment could not be processed.</p>

                    <div style="background: #fef2f2; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ef4444;">
                        <h3 style="margin-top: 0; color: #991b1b;">Payment Details</h3>

                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 10px; border-bottom: 1px solid #fecaca;"><strong>Reference:</strong></td>
                                <td style="padding: 10px; border-bottom: 1px solid #fecaca;">{reference}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border-bottom: 1px solid #fecaca;"><strong>Amount:</strong></td>
                                <td style="padding: 10px; border-bottom: 1px solid #fecaca;">${amount_usd:.2f}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border-bottom: 1px solid #fecaca;"><strong>Reason:</strong></td>
                                <td style="padding: 10px; border-bottom: 1px solid #fecaca;">{reason}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px;"><strong>Date:</strong></td>
                                <td style="padding: 10px;">{timestamp}</td>
                            </tr>
                        </table>
                    </div>

                    <p><strong>What you can do:</strong></p>
                    <ul>
                        <li>Check your payment method details</li>
                        <li>Ensure you have sufficient funds</li>
                        <li>Try again with a different payment method</li>
                        <li>Contact your bank if the issue persists</li>
                    </ul>

                    <p style="color: #6b7280; font-size: 12px; margin-top: 30px;">
                        If you need assistance, please contact our support team.
                    </p>
                </div>
            </body>
        </html>
        """

    def _create_refund_html(self, refund_details: Dict[str, Any]) -> str:

        """Create HTML for refund notification email.

        Args:
            refund_details: Refund details dictionary

        Returns:
            HTML email body
        """
        reference = refund_details.get("reference", "N/A")
        amount = refund_details.get("amount", 0)
        reason = refund_details.get("reason", "Refund processed")
        new_balance = refund_details.get("new_balance", 0)
        timestamp = refund_details.get("timestamp", datetime.now(timezone.utc).isoformat())

        return """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #10b981;">Refund Processed</h2>

                    <p>Your refund has been successfully processed.</p>

                    <div style="background: #f0fdf4; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #10b981;">
                        <h3 style="margin-top: 0; color: #065f46;">Refund Details</h3>

                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 10px; border-bottom: 1px solid #bbf7d0;"><strong>Reference:</strong></td>
                                <td style="padding: 10px; border-bottom: 1px solid #bbf7d0;">{reference}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border-bottom: 1px solid #bbf7d0;"><strong>Refund Amount:</strong></td>
                                <td style="padding: 10px; border-bottom: 1px solid #bbf7d0;">${amount:.2f}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border-bottom: 1px solid #bbf7d0;"><strong>Reason:</strong></td>
                                <td style="padding: 10px; border-bottom: 1px solid #bbf7d0;">{reason}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border-bottom: 1px solid #bbf7d0;"><strong>New Balance:</strong></td>
                                <td style="padding: 10px; border-bottom: 1px solid #bbf7d0;"><strong>{new_balance:.2f}</strong></td>
                            </tr>
                            <tr>
                                <td style="padding: 10px;"><strong>Date:</strong></td>
                                <td style="padding: 10px;">{timestamp}</td>
                            </tr>
                        </table>
                    </div>

                    <p>The refund will appear in your account within 3-5 business days.</p>

                    <p style="color: #6b7280; font-size: 12px; margin-top: 30px;">
                        If you have any questions, please contact our support team.
                    </p>
                </div>
            </body>
        </html>
        """


# Global instance
        email_service = EmailService()
