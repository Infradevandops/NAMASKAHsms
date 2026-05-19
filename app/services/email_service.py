"""Email service — uses Resend API if configured, falls back to SMTP."""

import asyncio
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

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
        self.from_name = "Vrenum"

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
            "Payment Receipt — Vrenum",
            self._receipt_html(payment_details),
        )

    async def send_payment_failed_alert(
        self, user_email: str, payment_details: Dict[str, Any]
    ) -> bool:
        return await self._send(
            user_email,
            "Payment Failed — Vrenum",
            self._failed_html(payment_details),
        )

    async def send_refund_notification(
        self, user_email: str, refund_details: Dict[str, Any]
    ) -> bool:
        return await self._send(
            user_email,
            "Refund Processed — Vrenum",
            self._refund_html(refund_details),
        )

    async def send_verification_email(
        self,
        user_email: str,
        verification_token: str,
        base_url: str = "https://vrenum.app",
    ) -> bool:
        verify_url = f"{base_url}/api/auth/verify-email?token={verification_token}"
        html = f"""
        <html>
        <body style="margin:0;padding:0;background:#f4f4f5;font-family:'Helvetica Neue',Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:40px 0;">
          <tr><td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
              <tr>
                <td style="background:linear-gradient(135deg,#FE3C72,#E0245E);padding:32px 40px;text-align:center;">
                  <h1 style="margin:0;color:#ffffff;font-size:28px;font-weight:800;">Vrenum</h1>
                  <p style="margin:4px 0 0;color:rgba(255,255,255,0.85);font-size:14px;">SMS Verification Platform</p>
                </td>
              </tr>
              <tr>
                <td style="padding:40px;">
                  <h2 style="margin:0 0 16px;color:#111827;font-size:22px;font-weight:700;">Verify your email address</h2>
                  <p style="margin:0 0 24px;color:#6b7280;font-size:15px;line-height:1.6;">
                    Welcome to Vrenum! Click the button below to verify your email and activate your account.
                  </p>
                  <table cellpadding="0" cellspacing="0" style="margin:0 0 32px;">
                    <tr>
                      <td style="background:linear-gradient(135deg,#FE3C72,#E0245E);border-radius:8px;">
                        <a href="{verify_url}" style="display:inline-block;padding:14px 32px;color:#ffffff;font-size:16px;font-weight:700;text-decoration:none;">Verify Email →</a>
                      </td>
                    </tr>
                  </table>
                  <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:16px 20px;">
                    <p style="margin:0;color:#166534;font-size:13px;">
                      ⏱ This link expires in <strong>24 hours</strong>.<br>
                      If you didn't create a Vrenum account, you can safely ignore this email.
                    </p>
                  </div>
                </td>
              </tr>
              <tr>
                <td style="background:#f9fafb;padding:24px 40px;border-top:1px solid #e5e7eb;text-align:center;">
                  <p style="margin:0;color:#9ca3af;font-size:12px;">
                    © 2026 Vrenum · <a href="https://vrenum.app" style="color:#9ca3af;">vrenum.app</a>
                  </p>
                </td>
              </tr>
            </table>
          </td></tr>
        </table>
        </body></html>
        """
        return await self._send(user_email, "Verify your Vrenum email", html)

    async def send_password_reset(
        self,
        user_email: str,
        reset_token: str,
        base_url: str = "https://vrenum.app",
    ) -> bool:
        reset_url = f"{base_url}/password-reset?token={reset_token}"
        html = f"""
        <html>
        <body style="margin:0;padding:0;background:#f4f4f5;font-family:'Helvetica Neue',Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:40px 0;">
          <tr><td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
              <!-- Header -->
              <tr>
                <td style="background:linear-gradient(135deg,#FE3C72,#E0245E);padding:32px 40px;text-align:center;">
                  <h1 style="margin:0;color:#ffffff;font-size:28px;font-weight:800;letter-spacing:-0.5px;">Vrenum</h1>
                  <p style="margin:4px 0 0;color:rgba(255,255,255,0.85);font-size:14px;">SMS Verification Platform</p>
                </td>
              </tr>
              <!-- Body -->
              <tr>
                <td style="padding:40px;">
                  <h2 style="margin:0 0 16px;color:#111827;font-size:22px;font-weight:700;">Reset your password</h2>
                  <p style="margin:0 0 24px;color:#6b7280;font-size:15px;line-height:1.6;">
                    We received a request to reset the password for your Vrenum account.
                    Click the button below to choose a new password.
                  </p>
                  <!-- CTA Button -->
                  <table cellpadding="0" cellspacing="0" style="margin:0 0 32px;">
                    <tr>
                      <td style="background:linear-gradient(135deg,#FE3C72,#E0245E);border-radius:8px;">
                        <a href="{reset_url}" style="display:inline-block;padding:14px 32px;color:#ffffff;font-size:16px;font-weight:700;text-decoration:none;border-radius:8px;">Reset Password →</a>
                      </td>
                    </tr>
                  </table>
                  <!-- Fallback link -->
                  <p style="margin:0 0 8px;color:#6b7280;font-size:13px;">Or copy this link into your browser:</p>
                  <p style="margin:0 0 32px;word-break:break-all;">
                    <a href="{reset_url}" style="color:#FE3C72;font-size:13px;">{reset_url}</a>
                  </p>
                  <!-- Warning box -->
                  <div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:16px 20px;">
                    <p style="margin:0;color:#92400e;font-size:13px;line-height:1.5;">
                      ⏱ This link expires in <strong>1 hour</strong>.<br>
                      If you didn't request a password reset, you can safely ignore this email.
                      Your password will not change.
                    </p>
                  </div>
                </td>
              </tr>
              <!-- Footer -->
              <tr>
                <td style="background:#f9fafb;padding:24px 40px;border-top:1px solid #e5e7eb;text-align:center;">
                  <p style="margin:0;color:#9ca3af;font-size:12px;">
                    © 2026 Vrenum · <a href="https://vrenum.app" style="color:#9ca3af;">vrenum.app</a> ·
                    <a href="https://vrenum.app/privacy" style="color:#9ca3af;">Privacy Policy</a>
                  </p>
                </td>
              </tr>
            </table>
          </td></tr>
        </table>
        </body></html>
        """
        return await self._send(user_email, "Reset your Vrenum password", html)

    # ── HTML templates ────────────────────────────────────────────────────────

    def _receipt_html(self, d: Dict[str, Any]) -> str:
        return f"""
        <html>
        <body style="margin:0;padding:0;background:#f4f4f5;font-family:'Helvetica Neue',Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:40px 0;">
          <tr><td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
              <tr>
                <td style="background:linear-gradient(135deg,#FE3C72,#E0245E);padding:32px 40px;text-align:center;">
                  <h1 style="margin:0;color:#ffffff;font-size:28px;font-weight:800;">Vrenum</h1>
                  <p style="margin:4px 0 0;color:rgba(255,255,255,0.85);font-size:14px;">Payment Receipt</p>
                </td>
              </tr>
              <tr>
                <td style="padding:40px;">
                  <h2 style="margin:0 0 8px;color:#111827;font-size:22px;font-weight:700;">✅ Payment Successful</h2>
                  <p style="margin:0 0 24px;color:#6b7280;font-size:15px;">Your account has been credited successfully.</p>
                  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;border-radius:12px;overflow:hidden;margin-bottom:24px;">
                    <tr style="border-bottom:1px solid #e5e7eb;">
                      <td style="padding:14px 20px;color:#6b7280;font-size:14px;">Reference</td>
                      <td style="padding:14px 20px;color:#111827;font-size:14px;font-weight:600;text-align:right;">{d.get('reference','N/A')}</td>
                    </tr>
                    <tr style="border-bottom:1px solid #e5e7eb;">
                      <td style="padding:14px 20px;color:#6b7280;font-size:14px;">Amount Paid</td>
                      <td style="padding:14px 20px;color:#111827;font-size:14px;font-weight:600;text-align:right;">${d.get('amount_usd',0):.2f}</td>
                    </tr>
                    <tr style="border-bottom:1px solid #e5e7eb;">
                      <td style="padding:14px 20px;color:#6b7280;font-size:14px;">Credits Added</td>
                      <td style="padding:14px 20px;color:#10b981;font-size:14px;font-weight:700;text-align:right;">+{d.get('credits_added',0):.2f}</td>
                    </tr>
                    <tr style="border-bottom:1px solid #e5e7eb;">
                      <td style="padding:14px 20px;color:#6b7280;font-size:14px;">New Balance</td>
                      <td style="padding:14px 20px;color:#FE3C72;font-size:16px;font-weight:800;text-align:right;">${d.get('new_balance',0):.2f}</td>
                    </tr>
                    <tr>
                      <td style="padding:14px 20px;color:#6b7280;font-size:14px;">Date</td>
                      <td style="padding:14px 20px;color:#111827;font-size:14px;text-align:right;">{d.get('timestamp', datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'))}</td>
                    </tr>
                  </table>
                  <table cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="background:linear-gradient(135deg,#FE3C72,#E0245E);border-radius:8px;">
                        <a href="https://vrenum.app/verify" style="display:inline-block;padding:12px 28px;color:#ffffff;font-size:15px;font-weight:700;text-decoration:none;">Start Verifying →</a>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
              <tr>
                <td style="background:#f9fafb;padding:24px 40px;border-top:1px solid #e5e7eb;text-align:center;">
                  <p style="margin:0;color:#9ca3af;font-size:12px;">© 2026 Vrenum · <a href="https://vrenum.app" style="color:#9ca3af;">vrenum.app</a></p>
                </td>
              </tr>
            </table>
          </td></tr>
        </table>
        </body></html>
        """

    def _failed_html(self, d: Dict[str, Any]) -> str:
        return f"""
        <html>
        <body style="margin:0;padding:0;background:#f4f4f5;font-family:'Helvetica Neue',Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:40px 0;">
          <tr><td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
              <tr>
                <td style="background:linear-gradient(135deg,#FE3C72,#E0245E);padding:32px 40px;text-align:center;">
                  <h1 style="margin:0;color:#ffffff;font-size:28px;font-weight:800;">Vrenum</h1>
                </td>
              </tr>
              <tr>
                <td style="padding:40px;">
                  <h2 style="margin:0 0 8px;color:#111827;font-size:22px;font-weight:700;">❌ Payment Failed</h2>
                  <p style="margin:0 0 24px;color:#6b7280;font-size:15px;">Your payment could not be processed.</p>
                  <table width="100%" cellpadding="0" cellspacing="0" style="background:#fef2f2;border-radius:12px;overflow:hidden;margin-bottom:24px;">
                    <tr style="border-bottom:1px solid #fecaca;">
                      <td style="padding:14px 20px;color:#6b7280;font-size:14px;">Reference</td>
                      <td style="padding:14px 20px;color:#111827;font-size:14px;font-weight:600;text-align:right;">{d.get('reference','N/A')}</td>
                    </tr>
                    <tr style="border-bottom:1px solid #fecaca;">
                      <td style="padding:14px 20px;color:#6b7280;font-size:14px;">Amount</td>
                      <td style="padding:14px 20px;color:#111827;font-size:14px;font-weight:600;text-align:right;">${d.get('amount_usd',0):.2f}</td>
                    </tr>
                    <tr>
                      <td style="padding:14px 20px;color:#6b7280;font-size:14px;">Reason</td>
                      <td style="padding:14px 20px;color:#ef4444;font-size:14px;font-weight:600;text-align:right;">{d.get('reason','Unknown')}</td>
                    </tr>
                  </table>
                  <table cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="background:linear-gradient(135deg,#FE3C72,#E0245E);border-radius:8px;">
                        <a href="https://vrenum.app/wallet" style="display:inline-block;padding:12px 28px;color:#ffffff;font-size:15px;font-weight:700;text-decoration:none;">Try Again →</a>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
              <tr>
                <td style="background:#f9fafb;padding:24px 40px;border-top:1px solid #e5e7eb;text-align:center;">
                  <p style="margin:0;color:#9ca3af;font-size:12px;">© 2026 Vrenum · <a href="https://vrenum.app" style="color:#9ca3af;">vrenum.app</a></p>
                </td>
              </tr>
            </table>
          </td></tr>
        </table>
        </body></html>
        """

    def _refund_html(self, d: Dict[str, Any]) -> str:
        return f"""
        <html>
        <body style="margin:0;padding:0;background:#f4f4f5;font-family:'Helvetica Neue',Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:40px 0;">
          <tr><td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
              <tr>
                <td style="background:linear-gradient(135deg,#FE3C72,#E0245E);padding:32px 40px;text-align:center;">
                  <h1 style="margin:0;color:#ffffff;font-size:28px;font-weight:800;">Vrenum</h1>
                </td>
              </tr>
              <tr>
                <td style="padding:40px;">
                  <h2 style="margin:0 0 8px;color:#111827;font-size:22px;font-weight:700;">🔄 Refund Processed</h2>
                  <p style="margin:0 0 24px;color:#6b7280;font-size:15px;">Your refund has been successfully processed and credited to your wallet.</p>
                  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0fdf4;border-radius:12px;overflow:hidden;margin-bottom:24px;">
                    <tr style="border-bottom:1px solid #bbf7d0;">
                      <td style="padding:14px 20px;color:#6b7280;font-size:14px;">Reference</td>
                      <td style="padding:14px 20px;color:#111827;font-size:14px;font-weight:600;text-align:right;">{d.get('reference','N/A')}</td>
                    </tr>
                    <tr style="border-bottom:1px solid #bbf7d0;">
                      <td style="padding:14px 20px;color:#6b7280;font-size:14px;">Refund Amount</td>
                      <td style="padding:14px 20px;color:#10b981;font-size:16px;font-weight:800;text-align:right;">+${d.get('amount',0):.2f}</td>
                    </tr>
                    <tr style="border-bottom:1px solid #bbf7d0;">
                      <td style="padding:14px 20px;color:#6b7280;font-size:14px;">Reason</td>
                      <td style="padding:14px 20px;color:#111827;font-size:14px;text-align:right;">{d.get('reason','Refund processed')}</td>
                    </tr>
                    <tr>
                      <td style="padding:14px 20px;color:#6b7280;font-size:14px;">New Balance</td>
                      <td style="padding:14px 20px;color:#FE3C72;font-size:16px;font-weight:800;text-align:right;">${d.get('new_balance',0):.2f}</td>
                    </tr>
                  </table>
                  <table cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="background:linear-gradient(135deg,#FE3C72,#E0245E);border-radius:8px;">
                        <a href="https://vrenum.app/verify" style="display:inline-block;padding:12px 28px;color:#ffffff;font-size:15px;font-weight:700;text-decoration:none;">Start New Verification →</a>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
              <tr>
                <td style="background:#f9fafb;padding:24px 40px;border-top:1px solid #e5e7eb;text-align:center;">
                  <p style="margin:0;color:#9ca3af;font-size:12px;">© 2026 Vrenum · <a href="https://vrenum.app" style="color:#9ca3af;">vrenum.app</a></p>
                </td>
              </tr>
            </table>
          </td></tr>
        </table>
        </body></html>
        """

    # ── Shared helpers ─────────────────────────────────────────────────────────

    def _unsub_footer(self) -> str:
        return (
            '<p style="margin:24px 0 0;color:#9ca3af;font-size:12px;">'
            "You received this because you have an account on Vrenum. "
            '<a href="https://vrenum.app/settings?tab=notifications" '
            'style="color:#9ca3af;">Manage preferences</a></p>'
        )

    def _greeting(self, user_name: Optional[str]) -> str:
        return (
            f'<p style="margin:0 0 8px;color:#6b7280;font-size:15px;">Hi {user_name},</p>'
            if user_name
            else ""
        )

    # ── Welcome email (Phase 8) ───────────────────────────────────────────────

    async def send_welcome_email(
        self,
        user_email: str,
        user_name: Optional[str] = None,
        base_url: str = "https://vrenum.app",
    ) -> bool:
        greeting = self._greeting(user_name)
        unsub = self._unsub_footer()
        html = f"""
        <html>
        <body style="margin:0;padding:0;background:#f4f4f5;font-family:'Helvetica Neue',Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:40px 0;">
          <tr><td align="center">
            <table width="600" cellpadding="0" cellspacing="0"
                   style="background:#ffffff;border-radius:16px;overflow:hidden;
                          box-shadow:0 4px 24px rgba(0,0,0,0.08);">
              <tr>
                <td style="background:linear-gradient(135deg,#FE3C72,#E0245E);
                           padding:32px 40px;text-align:center;">
                  <h1 style="margin:0;color:#ffffff;font-size:28px;font-weight:800;">Vrenum</h1>
                  <p style="margin:4px 0 0;color:rgba(255,255,255,0.85);font-size:14px;">
                    SMS Verification Platform
                  </p>
                </td>
              </tr>
              <tr>
                <td style="padding:40px;">
                  {greeting}
                  <h2 style="margin:0 0 16px;color:#111827;font-size:22px;font-weight:700;">
                    Welcome to Vrenum! 🎉
                  </h2>
                  <p style="margin:0 0 24px;color:#6b7280;font-size:15px;line-height:1.6;">
                    You're all set. Vrenum gives you instant phone numbers for SMS
                    verification across 1,800+ services in 200+ countries.
                  </p>
                  <div style="background:#f9fafb;border-radius:12px;padding:20px;margin-bottom:24px;">
                    <p style="margin:0 0 12px;font-weight:700;color:#111827;">Get started in 3 steps:</p>
                    <table width="100%" cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="padding:8px 0;color:#6b7280;font-size:14px;">
                          <span style="color:#FE3C72;font-weight:700;">1.</span>
                          Add credits to your wallet
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:8px 0;color:#6b7280;font-size:14px;">
                          <span style="color:#FE3C72;font-weight:700;">2.</span>
                          Select the service you want to verify
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:8px 0;color:#6b7280;font-size:14px;">
                          <span style="color:#FE3C72;font-weight:700;">3.</span>
                          Receive your SMS code instantly
                        </td>
                      </tr>
                    </table>
                  </div>
                  <table cellpadding="0" cellspacing="0" style="margin-bottom:24px;">
                    <tr>
                      <td style="background:linear-gradient(135deg,#FE3C72,#E0245E);border-radius:8px;">
                        <a href="{base_url}/verify"
                           style="display:inline-block;padding:14px 32px;color:#ffffff;
                                  font-size:16px;font-weight:700;text-decoration:none;">
                          Start Verifying →
                        </a>
                      </td>
                    </tr>
                  </table>
                  {unsub}
                </td>
              </tr>
              <tr>
                <td style="background:#f9fafb;padding:24px 40px;
                           border-top:1px solid #e5e7eb;text-align:center;">
                  <p style="margin:0;color:#9ca3af;font-size:12px;">
                    © 2026 Vrenum ·
                    <a href="https://vrenum.app" style="color:#9ca3af;">vrenum.app</a> ·
                    <a href="https://vrenum.app/privacy" style="color:#9ca3af;">Privacy Policy</a>
                  </p>
                </td>
              </tr>
            </table>
          </td></tr>
        </table>
        </body></html>
        """
        return await self._send(user_email, "Welcome to Vrenum 🎉", html)

    # ── Tier upgrade email (Phase 9) ──────────────────────────────────────────

    async def send_tier_upgrade_email(
        self,
        user_email: str,
        old_tier: str,
        new_tier: str,
        new_features: list,
        user_name: Optional[str] = None,
    ) -> bool:
        greeting = self._greeting(user_name)
        unsub = self._unsub_footer()
        features_html = "".join(
            f'<tr><td style="padding:8px 0;color:#6b7280;font-size:14px;">'
            f'<span style="color:#10b981;font-weight:700;">&#10003;</span> {f}</td></tr>'
            for f in new_features
        )
        tier_names = {
            "freemium": "Freemium",
            "payg": "Pay-As-You-Go",
            "pro": "Pro",
            "custom": "Custom",
        }
        old_display = tier_names.get(old_tier.lower(), old_tier.title())
        new_display = tier_names.get(new_tier.lower(), new_tier.title())
        html = f"""
        <html>
        <body style="margin:0;padding:0;background:#f4f4f5;font-family:'Helvetica Neue',Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:40px 0;">
          <tr><td align="center">
            <table width="600" cellpadding="0" cellspacing="0"
                   style="background:#ffffff;border-radius:16px;overflow:hidden;
                          box-shadow:0 4px 24px rgba(0,0,0,0.08);">
              <tr>
                <td style="background:linear-gradient(135deg,#FE3C72,#E0245E);
                           padding:32px 40px;text-align:center;">
                  <h1 style="margin:0;color:#ffffff;font-size:28px;font-weight:800;">Vrenum</h1>
                  <p style="margin:4px 0 0;color:rgba(255,255,255,0.85);font-size:14px;">
                    Plan Upgrade
                  </p>
                </td>
              </tr>
              <tr>
                <td style="padding:40px;">
                  {greeting}
                  <h2 style="margin:0 0 16px;color:#111827;font-size:22px;font-weight:700;">
                    You've upgraded to {new_display}! ⭐
                  </h2>
                  <p style="margin:0 0 24px;color:#6b7280;font-size:15px;line-height:1.6;">
                    Your plan has been upgraded from
                    <strong>{old_display}</strong> to <strong>{new_display}</strong>.
                    Here's what you've unlocked:
                  </p>
                  <div style="background:#f0fdf4;border-radius:12px;padding:20px;margin-bottom:24px;">
                    <table width="100%" cellpadding="0" cellspacing="0">
                      {features_html}
                    </table>
                  </div>
                  <table cellpadding="0" cellspacing="0" style="margin-bottom:24px;">
                    <tr>
                      <td style="background:linear-gradient(135deg,#FE3C72,#E0245E);border-radius:8px;">
                        <a href="https://vrenum.app/dashboard"
                           style="display:inline-block;padding:14px 32px;color:#ffffff;
                                  font-size:16px;font-weight:700;text-decoration:none;">
                          Go to Dashboard →
                        </a>
                      </td>
                    </tr>
                  </table>
                  {unsub}
                </td>
              </tr>
              <tr>
                <td style="background:#f9fafb;padding:24px 40px;
                           border-top:1px solid #e5e7eb;text-align:center;">
                  <p style="margin:0;color:#9ca3af;font-size:12px;">
                    © 2026 Vrenum ·
                    <a href="https://vrenum.app" style="color:#9ca3af;">vrenum.app</a>
                  </p>
                </td>
              </tr>
            </table>
          </td></tr>
        </table>
        </body></html>
        """
        return await self._send(
            user_email,
            f"You've upgraded to {new_display} — Vrenum",
            html,
        )


email_service = EmailService()
