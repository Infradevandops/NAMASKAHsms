"""Email notification service for sending notification emails."""


import asyncio
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.notification import Notification

logger = get_logger(__name__)


class EmailNotificationService:

    """Service for sending notification emails."""

    def __init__(self, db: Optional[Session] = None):

        """Initialize email notification service.

        Args:
            db: Database session (optional)
        """
        settings = get_settings()
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_email = settings.from_email
        self.enabled = bool(self.smtp_host and self.smtp_user and self.smtp_password)
        self.db = db

        if self.enabled:
            logger.info("Email notification service initialized")
        else:
            logger.warning("Email notification service not configured")

    async def send_notification_email(
        self,
        user_email: str,
        notification: Notification,
        unsubscribe_token: Optional[str] = None,
        ) -> bool:
        """Send notification email to user.

        Args:
            user_email: Recipient email address
            notification: Notification object
            unsubscribe_token: Token for unsubscribe link

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Email service not configured, skipping notification email")
        return False

        try:
            subject = f"[{notification.type.upper()}] {notification.title}"
            html_body = self._create_notification_html(
                notification=notification,
                unsubscribe_token=unsubscribe_token,
            )

            await self._send_email(to_email=user_email, subject=subject, html_body=html_body)

            logger.info(f"Notification email sent to {user_email} (type: {notification.type})")
        return True

        except Exception as e:
            logger.error(f"Failed to send notification email: {str(e)}")
        return False

    async def send_verification_initiated_email(
        self,
        user_email: str,
        service_name: str,
        verification_id: str,
        unsubscribe_token: Optional[str] = None,
        ) -> bool:
        """Send verification initiated email.

        Args:
            user_email: Recipient email address
            service_name: Name of service being verified
            verification_id: ID of verification
            unsubscribe_token: Token for unsubscribe link

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Email service not configured, skipping verification email")
        return False

        try:
            subject = "Verification Started - Namaskah SMS"
            html_body = self._create_verification_initiated_html(
                service_name=service_name,
                verification_id=verification_id,
                unsubscribe_token=unsubscribe_token,
            )

            await self._send_email(to_email=user_email, subject=subject, html_body=html_body)

            logger.info(f"Verification initiated email sent to {user_email} for {service_name}")
        return True

        except Exception as e:
            logger.error(f"Failed to send verification initiated email: {str(e)}")
        return False

    async def send_verification_completed_email(
        self,
        user_email: str,
        service_name: str,
        verification_id: str,
        cost: float,
        unsubscribe_token: Optional[str] = None,
        ) -> bool:
        """Send verification completed email.

        Args:
            user_email: Recipient email address
            service_name: Name of service verified
            verification_id: ID of verification
            cost: Cost of verification
            unsubscribe_token: Token for unsubscribe link

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Email service not configured, skipping verification email")
        return False

        try:
            subject = "Verification Completed - Namaskah SMS"
            html_body = self._create_verification_completed_html(
                service_name=service_name,
                verification_id=verification_id,
                cost=cost,
                unsubscribe_token=unsubscribe_token,
            )

            await self._send_email(to_email=user_email, subject=subject, html_body=html_body)

            logger.info(f"Verification completed email sent to {user_email} for {service_name}")
        return True

        except Exception as e:
            logger.error(f"Failed to send verification completed email: {str(e)}")
        return False

    async def send_low_balance_alert_email(
        self,
        user_email: str,
        current_balance: float,
        threshold: float,
        unsubscribe_token: Optional[str] = None,
        ) -> bool:
        """Send low balance alert email.

        Args:
            user_email: Recipient email address
            current_balance: Current account balance
            threshold: Low balance threshold
            unsubscribe_token: Token for unsubscribe link

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Email service not configured, skipping low balance email")
        return False

        try:
            subject = "Low Balance Alert - Namaskah SMS"
            html_body = self._create_low_balance_alert_html(
                current_balance=current_balance,
                threshold=threshold,
                unsubscribe_token=unsubscribe_token,
            )

            await self._send_email(to_email=user_email, subject=subject, html_body=html_body)

            logger.info(f"Low balance alert sent to {user_email}")
        return True

        except Exception as e:
            logger.error(f"Failed to send low balance alert: {str(e)}")
        return False

    async def send_daily_digest_email(
        self,
        user_email: str,
        notifications: List[Notification],
        unsubscribe_token: Optional[str] = None,
        ) -> bool:
        """Send daily digest email with multiple notifications.

        Args:
            user_email: Recipient email address
            notifications: List of notifications
            unsubscribe_token: Token for unsubscribe link

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Email service not configured, skipping digest email")
        return False

        if not notifications:
            logger.info("No notifications to send in digest")
        return False

        try:
            subject = f"Daily Digest - {len(notifications)} Updates - Namaskah SMS"
            html_body = self._create_daily_digest_html(
                notifications=notifications,
                unsubscribe_token=unsubscribe_token,
            )

            await self._send_email(to_email=user_email, subject=subject, html_body=html_body)

            logger.info(f"Daily digest sent to {user_email} with {len(notifications)} notifications")
        return True

        except Exception as e:
            logger.error(f"Failed to send daily digest: {str(e)}")
        return False

    async def send_weekly_digest_email(
        self,
        user_email: str,
        notifications: List[Notification],
        stats: Dict[str, Any],
        unsubscribe_token: Optional[str] = None,
        ) -> bool:
        """Send weekly digest email with statistics.

        Args:
            user_email: Recipient email address
            notifications: List of notifications
            stats: Weekly statistics
            unsubscribe_token: Token for unsubscribe link

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Email service not configured, skipping weekly digest email")
        return False

        if not notifications:
            logger.info("No notifications to send in weekly digest")
        return False

        try:
            subject = "Weekly Summary - Namaskah SMS"
            html_body = self._create_weekly_digest_html(
                notifications=notifications,
                stats=stats,
                unsubscribe_token=unsubscribe_token,
            )

            await self._send_email(to_email=user_email, subject=subject, html_body=html_body)

            logger.info(f"Weekly digest sent to {user_email}")
        return True

        except Exception as e:
            logger.error(f"Failed to send weekly digest: {str(e)}")
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

    def _create_notification_html(

        self,
        notification: Notification,
        unsubscribe_token: Optional[str] = None,
        ) -> str:
        """Create HTML for notification email.

        Args:
            notification: Notification object
            unsubscribe_token: Token for unsubscribe link

        Returns:
            HTML email body
        """
        unsubscribe_link = (
            f"https://namaskah.app/unsubscribe?token={unsubscribe_token}"
        if unsubscribe_token
            else "https://namaskah.app/preferences"
        )

        return """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #667eea;">{notification.title}</h2>

                    <p>{notification.message}</p>

                    {f'<p><a href="{notification.link}" style="color: #667eea; text-decoration: none;"><strong>View Details →</strong></a></p>' if notification.link else ''}

                    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

                    <p style="color: #6b7280; font-size: 12px;">
                        You received this email because you have notifications enabled for {notification.type}.
                        <a href="{unsubscribe_link}" style="color: #667eea; text-decoration: none;">Manage preferences</a>
                    </p>
                </div>
            </body>
        </html>
        """

    def _create_verification_initiated_html(

        self,
        service_name: str,
        verification_id: str,
        unsubscribe_token: Optional[str] = None,
        ) -> str:
        """Create HTML for verification initiated email.

        Args:
            service_name: Name of service
            verification_id: ID of verification
            unsubscribe_token: Token for unsubscribe link

        Returns:
            HTML email body
        """
        unsubscribe_link = (
            f"https://namaskah.app/unsubscribe?token={unsubscribe_token}"
        if unsubscribe_token
            else "https://namaskah.app/preferences"
        )

        return """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #667eea;">🚀 Verification Started</h2>

                    <p>Your verification for <strong>{service_name}</strong> has been initiated.</p>

                    <div style="background: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <p><strong>What's next?</strong></p>
                        <ul>
                            <li>You will receive an SMS code shortly</li>
                            <li>Enter the code in the Namaskah app to complete verification</li>
                            <li>Verification typically completes within 2-5 minutes</li>
                        </ul>
                    </div>

                    <p>
                        <a href="https://namaskah.app/verify?id={verification_id}" style="display: inline-block; background: #667eea; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none;">
                            View Verification Status
                        </a>
                    </p>

                    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

                    <p style="color: #6b7280; font-size: 12px;">
                        <a href="{unsubscribe_link}" style="color: #667eea; text-decoration: none;">Manage notification preferences</a>
                    </p>
                </div>
            </body>
        </html>
        """

    def _create_verification_completed_html(

        self,
        service_name: str,
        verification_id: str,
        cost: float,
        unsubscribe_token: Optional[str] = None,
        ) -> str:
        """Create HTML for verification completed email.

        Args:
            service_name: Name of service
            verification_id: ID of verification
            cost: Cost of verification
            unsubscribe_token: Token for unsubscribe link

        Returns:
            HTML email body
        """
        unsubscribe_link = (
            f"https://namaskah.app/unsubscribe?token={unsubscribe_token}"
        if unsubscribe_token
            else "https://namaskah.app/preferences"
        )

        return """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #10b981;">✅ Verification Completed</h2>

                    <p>Your verification for <strong>{service_name}</strong> has been completed successfully!</p>

                    <div style="background: #f0fdf4; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #10b981;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 10px;"><strong>Service:</strong></td>
                                <td style="padding: 10px;">{service_name}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px;"><strong>Cost:</strong></td>
                                <td style="padding: 10px;">${cost:.2f}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px;"><strong>Date:</strong></td>
                                <td style="padding: 10px;">{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC</td>
                            </tr>
                        </table>
                    </div>

                    <p>You can now use this verified account on {service_name}.</p>

                    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

                    <p style="color: #6b7280; font-size: 12px;">
                        <a href="{unsubscribe_link}" style="color: #667eea; text-decoration: none;">Manage notification preferences</a>
                    </p>
                </div>
            </body>
        </html>
        """

    def _create_low_balance_alert_html(

        self,
        current_balance: float,
        threshold: float,
        unsubscribe_token: Optional[str] = None,
        ) -> str:
        """Create HTML for low balance alert email.

        Args:
            current_balance: Current balance
            threshold: Low balance threshold
            unsubscribe_token: Token for unsubscribe link

        Returns:
            HTML email body
        """
        unsubscribe_link = (
            f"https://namaskah.app/unsubscribe?token={unsubscribe_token}"
        if unsubscribe_token
            else "https://namaskah.app/preferences"
        )

        return """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #f59e0b;">⚠️ Low Balance Alert</h2>

                    <p>Your account balance is running low.</p>

                    <div style="background: #fffbeb; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #f59e0b;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 10px;"><strong>Current Balance:</strong></td>
                                <td style="padding: 10px; color: #f59e0b;"><strong>${current_balance:.2f}</strong></td>
                            </tr>
                            <tr>
                                <td style="padding: 10px;"><strong>Alert Threshold:</strong></td>
                                <td style="padding: 10px;">${threshold:.2f}</td>
                            </tr>
                        </table>
                    </div>

                    <p>
                        <a href="https://namaskah.app/wallet" style="display: inline-block; background: #667eea; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none;">
                            Add Credits
                        </a>
                    </p>

                    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

                    <p style="color: #6b7280; font-size: 12px;">
                        <a href="{unsubscribe_link}" style="color: #667eea; text-decoration: none;">Manage notification preferences</a>
                    </p>
                </div>
            </body>
        </html>
        """

    def _create_daily_digest_html(

        self,
        notifications: List[Notification],
        unsubscribe_token: Optional[str] = None,
        ) -> str:
        """Create HTML for daily digest email.

        Args:
            notifications: List of notifications
            unsubscribe_token: Token for unsubscribe link

        Returns:
            HTML email body
        """
        unsubscribe_link = (
            f"https://namaskah.app/unsubscribe?token={unsubscribe_token}"
        if unsubscribe_token
            else "https://namaskah.app/preferences"
        )

        notifications_html = "".join(
            [
                """
            <div style="background: #f9fafb; padding: 15px; border-radius: 6px; margin: 10px 0; border-left: 4px solid #667eea;">
                <h4 style="margin: 0 0 8px 0; color: #667eea;">{n.title}</h4>
                <p style="margin: 0; color: #6b7280; font-size: 14px;">{n.message}</p>
                <p style="margin: 8px 0 0 0; font-size: 12px; color: #9ca3af;">{n.created_at.strftime('%Y-%m-%d %H:%M:%S') if n.created_at else 'N/A'}</p>
            </div>
            """
        for n in notifications
            ]
        )

        return """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #667eea;">📬 Daily Digest</h2>

                    <p>Here's a summary of your notifications from today:</p>

                    <div style="margin: 20px 0;">
                        {notifications_html}
                    </div>

                    <p>
                        <a href="https://namaskah.app/notifications" style="display: inline-block; background: #667eea; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none;">
                            View All Notifications
                        </a>
                    </p>

                    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

                    <p style="color: #6b7280; font-size: 12px;">
                        <a href="{unsubscribe_link}" style="color: #667eea; text-decoration: none;">Manage notification preferences</a>
                    </p>
                </div>
            </body>
        </html>
        """

    def _create_weekly_digest_html(

        self,
        notifications: List[Notification],
        stats: Dict[str, Any],
        unsubscribe_token: Optional[str] = None,
        ) -> str:
        """Create HTML for weekly digest email.

        Args:
            notifications: List of notifications
            stats: Weekly statistics
            unsubscribe_token: Token for unsubscribe link

        Returns:
            HTML email body
        """
        unsubscribe_link = (
            f"https://namaskah.app/unsubscribe?token={unsubscribe_token}"
        if unsubscribe_token
            else "https://namaskah.app/preferences"
        )

        notifications_html = "".join(
            [
                """
            <div style="background: #f9fafb; padding: 15px; border-radius: 6px; margin: 10px 0; border-left: 4px solid #667eea;">
                <h4 style="margin: 0 0 8px 0; color: #667eea;">{n.title}</h4>
                <p style="margin: 0; color: #6b7280; font-size: 14px;">{n.message}</p>
            </div>
            """
        for n in notifications[:10]
            ]
        )

        stats_html = "".join(
            [
                """
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;"><strong>{key.replace('_', ' ').title()}:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{value}</td>
            </tr>
            """
        for key, value in stats.items()
            ]
        )

        return """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #667eea;">📊 Weekly Summary</h2>

                    <p>Here's your weekly activity summary:</p>

                    <div style="background: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">Statistics</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            {stats_html}
                        </table>
                    </div>

                    <div style="margin: 20px 0;">
                        <h3>Recent Notifications</h3>
                        {notifications_html}
                        {f'<p style="color: #6b7280; font-size: 12px;">... and {len(notifications) - 10} more</p>' if len(notifications) > 10 else ''}
                    </div>

                    <p>
                        <a href="https://namaskah.app/notifications" style="display: inline-block; background: #667eea; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none;">
                            View All Notifications
                        </a>
                    </p>

                    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

                    <p style="color: #6b7280; font-size: 12px;">
                        <a href="{unsubscribe_link}" style="color: #667eea; text-decoration: none;">Manage notification preferences</a>
                    </p>
                </div>
            </body>
        </html>
        """
