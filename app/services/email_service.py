"""Email service — uses Resend API if configured, falls back to SMTP."""

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
    """Sends emails via Resend (preferred) or SMTP (fallback)."""

    def __init__(self):
        settings = get_settings()
        self.resend_api_key = settings.resend_api_key
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_username or "onboarding@resend.dev"
        self.from_name = "Namaskah"

        if self.resend_api_key:
            # Lazy-load resend to avoid import errors if package is not installed
            # The actual import will happen in _send_resend when needed
            self.enabled = True
            self._mode = "resend"
            logger.info("Email service initialised — Resend (lazy-loaded)")
        elif self.smtp_host and self.smtp_user and self.smtp_password:
            self.enabled = True
            self._mode = "smtp"
            logger.info("Email service initialised — SMTP")
        else:
            self.enabled = False
            self._mode = None
            logger.warning("Email service not configured")

    async def _send(self, to_email: str, subject: str, html_body: str) -> bool:
        if not self.enabled:
            logger.warning("Email service not configured, skipping send")
            return False
        try:
            if self._mode == "resend":
                return await self._send_resend(to_email, subject, html_body)
            return await self._send_smtp(to_email, subject, html_body)
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def _send_resend(self, to_email: str, subject: str, html_body: str) -> bool:
        import resend

        resend.api_key = self.resend_api_key
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: resend.Emails.send(
                {
                    "from": f"{self.from_name} <{self.from_email}>",
                    "to": [to_email],
                    "subject": subject,
                    "html": html_body,
                }
            ),
        )
        logger.info(f"Email sent via Resend to {to_email}: {subject}")
        return True

    async def _send_smtp(self, to_email: str, subject: str, html_body: str) -> bool:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.from_email
        message["To"] = to_email
        message.attach(MIMEText(html_body, "html"))
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._smtp_send, to_email, message.as_string())
        logger.info(f"Email sent via SMTP to {to_email}: {subject}")
        return True

    def _smtp_send(self, to_email: str, message: str) -> None:
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.from_email, to_email, message)

    # ── Public methods ────────────────────────────────────────────────────────

    async def send_payment_receipt(
        self, user_email: str, payment_details: Dict[str, Any]
    ) -> bool:
        return await self._send(
            user_email,
            "Payment Receipt — Namaskah",
            self._receipt_html(payment_details),
        )

    async def send_payment_failed_alert(
        self, user_email: str, payment_details: Dict[str, Any]
    ) -> bool:
        return await self._send(
            user_email,
            "Payment Failed — Namaskah",
            self._failed_html(payment_details),
        )

    async def send_refund_notification(
        self, user_email: str, refund_details: Dict[str, Any]
    ) -> bool:
        return await self._send(
            user_email,
            "Refund Processed — Namaskah",
            self._refund_html(refund_details),
        )

    async def send_verification_email(
        self,
        user_email: str,
        verification_token: str,
        base_url: str = "https://namaskah.onrender.com",
    ) -> bool:
        verify_url = f"{base_url}/api/auth/verify-email?token={verification_token}"
        html = f"""
        <html><body style="font-family:Arial,sans-serif;color:#333;">
        <div style="max-width:600px;margin:0 auto;padding:20px;">
            <h2 style="color:#667eea;">Verify your email</h2>
            <p>Click the button below to verify your Namaskah account.</p>
            <a href="{verify_url}" style="display:inline-block;padding:12px 24px;background:#667eea;color:#fff;text-decoration:none;border-radius:6px;margin:20px 0;">Verify Email</a>
            <p style="color:#999;font-size:12px;">Link expires in 24 hours. If you didn't create an account, ignore this email.</p>
        </div>
        </body></html>
        """
        return await self._send(user_email, "Verify your Namaskah email", html)

    async def send_password_reset(
        self,
        user_email: str,
        reset_token: str,
        base_url: str = "https://namaskah.onrender.com",
    ) -> bool:
        reset_url = f"{base_url}/reset-password?token={reset_token}"
        html = f"""
        <html><body style="font-family:Arial,sans-serif;color:#333;">
        <div style="max-width:600px;margin:0 auto;padding:20px;">
            <h2 style="color:#667eea;">Reset your password</h2>
            <p>Click the button below to reset your Namaskah password.</p>
            <a href="{reset_url}" style="display:inline-block;padding:12px 24px;background:#667eea;color:#fff;text-decoration:none;border-radius:6px;margin:20px 0;">Reset Password</a>
            <p style="color:#999;font-size:12px;">Link expires in 1 hour. If you didn't request this, ignore this email.</p>
        </div>
        </body></html>
        """
        return await self._send(user_email, "Reset your Namaskah password", html)

    # ── HTML templates ────────────────────────────────────────────────────────

    def _receipt_html(self, d: Dict[str, Any]) -> str:
        return f"""
        <html><body style="font-family:Arial,sans-serif;color:#333;">
        <div style="max-width:600px;margin:0 auto;padding:20px;">
            <h2 style="color:#667eea;">Payment Receipt</h2>
            <p>Your account has been credited successfully.</p>
            <div style="background:#f9fafb;padding:20px;border-radius:8px;margin:20px 0;">
                <table style="width:100%;border-collapse:collapse;">
                    <tr><td><strong>Reference:</strong></td><td>{d.get('reference','N/A')}</td></tr>
                    <tr><td><strong>Amount Paid:</strong></td><td>${d.get('amount_usd',0):.2f}</td></tr>
                    <tr><td><strong>Credits Added:</strong></td><td>{d.get('credits_added',0):.2f}</td></tr>
                    <tr><td><strong>New Balance:</strong></td><td><strong>{d.get('new_balance',0):.2f}</strong></td></tr>
                    <tr><td><strong>Date:</strong></td><td>{d.get('timestamp', datetime.now(timezone.utc).isoformat())}</td></tr>
                </table>
            </div>
        </div></body></html>
        """

    def _failed_html(self, d: Dict[str, Any]) -> str:
        return f"""
        <html><body style="font-family:Arial,sans-serif;color:#333;">
        <div style="max-width:600px;margin:0 auto;padding:20px;">
            <h2 style="color:#ef4444;">Payment Failed</h2>
            <p>Your payment could not be processed.</p>
            <div style="background:#fef2f2;padding:20px;border-radius:8px;margin:20px 0;">
                <table style="width:100%;border-collapse:collapse;">
                    <tr><td><strong>Reference:</strong></td><td>{d.get('reference','N/A')}</td></tr>
                    <tr><td><strong>Amount:</strong></td><td>${d.get('amount_usd',0):.2f}</td></tr>
                    <tr><td><strong>Reason:</strong></td><td>{d.get('reason','Unknown')}</td></tr>
                    <tr><td><strong>Date:</strong></td><td>{d.get('timestamp', datetime.now(timezone.utc).isoformat())}</td></tr>
                </table>
            </div>
        </div></body></html>
        """

    def _refund_html(self, d: Dict[str, Any]) -> str:
        return f"""
        <html><body style="font-family:Arial,sans-serif;color:#333;">
        <div style="max-width:600px;margin:0 auto;padding:20px;">
            <h2 style="color:#10b981;">Refund Processed</h2>
            <p>Your refund has been successfully processed.</p>
            <div style="background:#f0fdf4;padding:20px;border-radius:8px;margin:20px 0;">
                <table style="width:100%;border-collapse:collapse;">
                    <tr><td><strong>Reference:</strong></td><td>{d.get('reference','N/A')}</td></tr>
                    <tr><td><strong>Refund Amount:</strong></td><td>${d.get('amount',0):.2f}</td></tr>
                    <tr><td><strong>Reason:</strong></td><td>{d.get('reason','Refund processed')}</td></tr>
                    <tr><td><strong>New Balance:</strong></td><td><strong>{d.get('new_balance',0):.2f}</strong></td></tr>
                    <tr><td><strong>Date:</strong></td><td>{d.get('timestamp', datetime.now(timezone.utc).isoformat())}</td></tr>
                </table>
            </div>
        </div></body></html>
        """


email_service = EmailService()
