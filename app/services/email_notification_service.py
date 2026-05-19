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

# Shared branded email wrapper
_HEADER = """
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
      <tr><td style="padding:40px;">
"""

_FOOTER = """
      </td></tr>
      <tr>
        <td style="background:#f9fafb;padding:24px 40px;
                   border-top:1px solid #e5e7eb;text-align:center;">
          <p style="margin:0;color:#9ca3af;font-size:12px;">
            &copy; 2026 Vrenum &middot;
            <a href="https://vrenum.app" style="color:#9ca3af;">vrenum.app</a>
            &middot;
            <a href="https://vrenum.app/privacy" style="color:#9ca3af;">Privacy Policy</a>
          </p>
        </td>
      </tr>
    </table>
  </td></tr>
</table>
</body></html>
"""

_PINK_BTN = (
    '<table cellpadding="0" cellspacing="0" style="margin:24px 0;">'
    '<tr><td style="background:linear-gradient(135deg,#FE3C72,#E0245E);'
    'border-radius:8px;">'
    '<a href="{url}" style="display:inline-block;padding:13px 28px;'
    'color:#ffffff;font-size:15px;font-weight:700;text-decoration:none;">'
    "{label}</a></td></tr></table>"
)

_UNSUB = (
    '<p style="margin:24px 0 0;color:#9ca3af;font-size:12px;">'
    "You received this because you have email notifications enabled. "
    '<a href="{link}" style="color:#9ca3af;">Manage preferences</a></p>'
)


def _unsub_link(token: Optional[str]) -> str:
    if token:
        return f"https://vrenum.app/unsubscribe?token={token}"
    return "https://vrenum.app/settings?tab=notifications"


class EmailNotificationService:
    """Service for sending notification emails."""

    def __init__(self, db: Optional[Session] = None):
        settings = get_settings()
        self.resend_api_key = settings.resend_api_key
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.from_email = settings.from_email
        self.db = db

        if self.resend_api_key:
            import resend

            resend.api_key = self.resend_api_key
            self.enabled = True
            self._mode = "resend"
            logger.info("Email notification service initialised — Resend")
        elif self.smtp_host and self.smtp_user and self.smtp_password:
            self.enabled = True
            self._mode = "smtp"
            logger.info("Email notification service initialised — SMTP")
        else:
            self.enabled = False
            self._mode = None
            logger.warning("Email notification service not configured")

    # ── Public send methods ───────────────────────────────────────────────────

    async def send_notification_email(
        self,
        user_email: str,
        notification: Notification,
        user_name: Optional[str] = None,
        unsubscribe_token: Optional[str] = None,
    ) -> bool:
        if not self.enabled:
            logger.warning("Email service not configured, skipping notification email")
            return False
        try:
            subject = f"[{notification.type.upper()}] {notification.title}"
            html_body = self._create_notification_html(
                notification=notification,
                user_name=user_name,
                unsubscribe_token=unsubscribe_token,
            )
            await self._send_email(
                to_email=user_email, subject=subject, html_body=html_body
            )
            logger.info(
                f"Notification email sent to {user_email} (type: {notification.type})"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send notification email: {str(e)}")
            return False

    async def send_verification_initiated_email(
        self,
        user_email: str,
        service_name: str,
        verification_id: str,
        user_name: Optional[str] = None,
        unsubscribe_token: Optional[str] = None,
    ) -> bool:
        if not self.enabled:
            logger.warning("Email service not configured, skipping verification email")
            return False
        try:
            subject = f"Your {service_name} verification has started — Vrenum"
            html_body = self._create_verification_initiated_html(
                service_name=service_name,
                verification_id=verification_id,
                user_name=user_name,
                unsubscribe_token=unsubscribe_token,
            )
            await self._send_email(
                to_email=user_email, subject=subject, html_body=html_body
            )
            logger.info(
                f"Verification initiated email sent to {user_email} for {service_name}"
            )
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
        user_name: Optional[str] = None,
        unsubscribe_token: Optional[str] = None,
    ) -> bool:
        if not self.enabled:
            logger.warning("Email service not configured, skipping verification email")
            return False
        try:
            subject = f"✅ {service_name} verification complete — Vrenum"
            html_body = self._create_verification_completed_html(
                service_name=service_name,
                verification_id=verification_id,
                cost=cost,
                user_name=user_name,
                unsubscribe_token=unsubscribe_token,
            )
            await self._send_email(
                to_email=user_email, subject=subject, html_body=html_body
            )
            logger.info(
                f"Verification completed email sent to {user_email} for {service_name}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send verification completed email: {str(e)}")
            return False

    async def send_low_balance_alert_email(
        self,
        user_email: str,
        current_balance: float,
        threshold: float,
        user_name: Optional[str] = None,
        unsubscribe_token: Optional[str] = None,
    ) -> bool:
        if not self.enabled:
            logger.warning("Email service not configured, skipping low balance email")
            return False
        try:
            subject = "⚠️ Your Vrenum balance is running low"
            html_body = self._create_low_balance_alert_html(
                current_balance=current_balance,
                threshold=threshold,
                user_name=user_name,
                unsubscribe_token=unsubscribe_token,
            )
            await self._send_email(
                to_email=user_email, subject=subject, html_body=html_body
            )
            logger.info(f"Low balance alert sent to {user_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send low balance alert: {str(e)}")
            return False

    async def send_daily_digest_email(
        self,
        user_email: str,
        notifications: List[Notification],
        user_name: Optional[str] = None,
        unsubscribe_token: Optional[str] = None,
    ) -> bool:
        if not self.enabled:
            logger.warning("Email service not configured, skipping digest email")
            return False
        if not notifications:
            logger.info("No notifications to send in digest")
            return False
        try:
            subject = f"📬 Your daily digest — {len(notifications)} update{'s' if len(notifications) != 1 else ''}"
            html_body = self._create_daily_digest_html(
                notifications=notifications,
                user_name=user_name,
                unsubscribe_token=unsubscribe_token,
            )
            await self._send_email(
                to_email=user_email, subject=subject, html_body=html_body
            )
            logger.info(
                f"Daily digest sent to {user_email} with {len(notifications)} notifications"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send daily digest: {str(e)}")
            return False

    async def send_weekly_digest_email(
        self,
        user_email: str,
        notifications: List[Notification],
        stats: Dict[str, Any],
        user_name: Optional[str] = None,
        unsubscribe_token: Optional[str] = None,
    ) -> bool:
        if not self.enabled:
            logger.warning("Email service not configured, skipping weekly digest email")
            return False
        if not notifications:
            logger.info("No notifications to send in weekly digest")
            return False
        try:
            subject = "📊 Your weekly Vrenum summary"
            html_body = self._create_weekly_digest_html(
                notifications=notifications,
                stats=stats,
                user_name=user_name,
                unsubscribe_token=unsubscribe_token,
            )
            await self._send_email(
                to_email=user_email, subject=subject, html_body=html_body
            )
            logger.info(f"Weekly digest sent to {user_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send weekly digest: {str(e)}")
            return False

    # ── Transport ─────────────────────────────────────────────────────────────

    async def _send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        try:
            if self._mode == "resend":
                import resend

                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: resend.Emails.send(
                        {
                            "from": f"Vrenum <{self.from_email}>",
                            "to": [to_email],
                            "subject": subject,
                            "html": html_body,
                        }
                    ),
                )
                return True

            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email
            message.attach(MIMEText(html_body, "html"))
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, self._send_smtp, to_email, message.as_string()
            )
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def _send_smtp(self, to_email: str, message: str) -> None:
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to_email, message)
        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            raise

    # ── HTML builders ─────────────────────────────────────────────────────────

    def _create_notification_html(
        self,
        notification: Notification,
        user_name: Optional[str] = None,
        unsubscribe_token: Optional[str] = None,
    ) -> str:
        greeting = f"Hi {user_name}," if user_name else "Hi there,"
        link_html = (
            _PINK_BTN.format(url=notification.link, label="View Details →")
            if notification.link
            else ""
        )
        unsub = _UNSUB.format(link=_unsub_link(unsubscribe_token))
        body = f"""
          <p style="margin:0 0 8px;color:#6b7280;font-size:15px;">{greeting}</p>
          <h2 style="margin:0 0 16px;color:#111827;font-size:22px;font-weight:700;">
            {notification.title}
          </h2>
          <p style="margin:0 0 24px;color:#6b7280;font-size:15px;line-height:1.6;">
            {notification.message}
          </p>
          {link_html}
          {unsub}
        """
        return _HEADER + body + _FOOTER

    def _create_verification_initiated_html(
        self,
        service_name: str,
        verification_id: str,
        user_name: Optional[str] = None,
        unsubscribe_token: Optional[str] = None,
    ) -> str:
        greeting = f"Hi {user_name}," if user_name else "Hi there,"
        status_url = f"https://vrenum.app/verify?id={verification_id}"
        btn = _PINK_BTN.format(url=status_url, label="View Verification Status →")
        unsub = _UNSUB.format(link=_unsub_link(unsubscribe_token))
        body = f"""
          <p style="margin:0 0 8px;color:#6b7280;font-size:15px;">{greeting}</p>
          <h2 style="margin:0 0 16px;color:#111827;font-size:22px;font-weight:700;">
            🚀 Verification Started
          </h2>
          <p style="margin:0 0 24px;color:#6b7280;font-size:15px;line-height:1.6;">
            Your <strong>{service_name}</strong> verification has been initiated.
            We're scanning for your SMS code now.
          </p>
          <div style="background:#f9fafb;border-radius:12px;padding:20px;margin-bottom:24px;">
            <p style="margin:0 0 12px;font-weight:700;color:#111827;">What happens next?</p>
            <ul style="margin:0;padding-left:20px;color:#6b7280;font-size:14px;line-height:1.8;">
              <li>You'll receive an SMS code on the assigned number</li>
              <li>Enter the code on the service you're verifying</li>
              <li>Verification typically completes within 2–5 minutes</li>
            </ul>
          </div>
          {btn}
          {unsub}
        """
        return _HEADER + body + _FOOTER

    def _create_verification_completed_html(
        self,
        service_name: str,
        verification_id: str,
        cost: float,
        user_name: Optional[str] = None,
        unsubscribe_token: Optional[str] = None,
    ) -> str:
        greeting = f"Hi {user_name}," if user_name else "Hi there,"
        completed_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        btn = _PINK_BTN.format(
            url="https://vrenum.app/verify", label="Start New Verification →"
        )
        unsub = _UNSUB.format(link=_unsub_link(unsubscribe_token))
        body = f"""
          <p style="margin:0 0 8px;color:#6b7280;font-size:15px;">{greeting}</p>
          <h2 style="margin:0 0 16px;color:#111827;font-size:22px;font-weight:700;">
            ✅ Verification Complete
          </h2>
          <p style="margin:0 0 24px;color:#6b7280;font-size:15px;line-height:1.6;">
            Your <strong>{service_name}</strong> verification was successful.
          </p>
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="background:#f0fdf4;border-radius:12px;overflow:hidden;margin-bottom:24px;">
            <tr style="border-bottom:1px solid #bbf7d0;">
              <td style="padding:14px 20px;color:#6b7280;font-size:14px;">Service</td>
              <td style="padding:14px 20px;color:#111827;font-size:14px;
                         font-weight:600;text-align:right;">{service_name}</td>
            </tr>
            <tr style="border-bottom:1px solid #bbf7d0;">
              <td style="padding:14px 20px;color:#6b7280;font-size:14px;">Cost</td>
              <td style="padding:14px 20px;color:#FE3C72;font-size:14px;
                         font-weight:700;text-align:right;">${cost:.2f}</td>
            </tr>
            <tr>
              <td style="padding:14px 20px;color:#6b7280;font-size:14px;">Completed</td>
              <td style="padding:14px 20px;color:#111827;font-size:14px;
                         text-align:right;">{completed_at}</td>
            </tr>
          </table>
          {btn}
          {unsub}
        """
        return _HEADER + body + _FOOTER

    def _create_low_balance_alert_html(
        self,
        current_balance: float,
        threshold: float,
        user_name: Optional[str] = None,
        unsubscribe_token: Optional[str] = None,
    ) -> str:
        greeting = f"Hi {user_name}," if user_name else "Hi there,"
        btn = _PINK_BTN.format(url="https://vrenum.app/wallet", label="Add Credits →")
        unsub = _UNSUB.format(link=_unsub_link(unsubscribe_token))
        body = f"""
          <p style="margin:0 0 8px;color:#6b7280;font-size:15px;">{greeting}</p>
          <h2 style="margin:0 0 16px;color:#111827;font-size:22px;font-weight:700;">
            ⚠️ Low Balance Alert
          </h2>
          <p style="margin:0 0 24px;color:#6b7280;font-size:15px;line-height:1.6;">
            Your Vrenum account balance is running low. Top up now to keep
            verifying without interruption.
          </p>
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="background:#fffbeb;border-radius:12px;overflow:hidden;margin-bottom:24px;">
            <tr style="border-bottom:1px solid #fde68a;">
              <td style="padding:14px 20px;color:#6b7280;font-size:14px;">Current Balance</td>
              <td style="padding:14px 20px;color:#f59e0b;font-size:16px;
                         font-weight:800;text-align:right;">${current_balance:.2f}</td>
            </tr>
            <tr>
              <td style="padding:14px 20px;color:#6b7280;font-size:14px;">Alert Threshold</td>
              <td style="padding:14px 20px;color:#111827;font-size:14px;
                         text-align:right;">${threshold:.2f}</td>
            </tr>
          </table>
          {btn}
          {unsub}
        """
        return _HEADER + body + _FOOTER

    def _create_daily_digest_html(
        self,
        notifications: List[Notification],
        user_name: Optional[str] = None,
        unsubscribe_token: Optional[str] = None,
    ) -> str:
        greeting = f"Hi {user_name}," if user_name else "Hi there,"
        items_html = "".join(
            f"""
            <div style="background:#f9fafb;border-radius:10px;padding:16px;
                        margin-bottom:12px;border-left:4px solid #FE3C72;">
              <p style="margin:0 0 4px;font-weight:700;color:#111827;font-size:14px;">
                {n.title}
              </p>
              <p style="margin:0 0 6px;color:#6b7280;font-size:13px;line-height:1.5;">
                {n.message}
              </p>
              <p style="margin:0;color:#9ca3af;font-size:11px;">
                {n.created_at.strftime('%Y-%m-%d %H:%M UTC') if n.created_at else ''}
              </p>
            </div>
            """
            for n in notifications
        )
        btn = _PINK_BTN.format(
            url="https://vrenum.app/notifications", label="View All Notifications →"
        )
        unsub = _UNSUB.format(link=_unsub_link(unsubscribe_token))
        body = f"""
          <p style="margin:0 0 8px;color:#6b7280;font-size:15px;">{greeting}</p>
          <h2 style="margin:0 0 16px;color:#111827;font-size:22px;font-weight:700;">
            📬 Your Daily Digest
          </h2>
          <p style="margin:0 0 24px;color:#6b7280;font-size:15px;">
            You have <strong>{len(notifications)}</strong>
            update{'s' if len(notifications) != 1 else ''} from today.
          </p>
          {items_html}
          {btn}
          {unsub}
        """
        return _HEADER + body + _FOOTER

    def _create_weekly_digest_html(
        self,
        notifications: List[Notification],
        stats: Dict[str, Any],
        user_name: Optional[str] = None,
        unsubscribe_token: Optional[str] = None,
    ) -> str:
        greeting = f"Hi {user_name}," if user_name else "Hi there,"
        stats_rows = "".join(
            f"""
            <tr style="border-bottom:1px solid #e5e7eb;">
              <td style="padding:12px 20px;color:#6b7280;font-size:14px;">
                {k.replace('_', ' ').title()}
              </td>
              <td style="padding:12px 20px;color:#111827;font-size:14px;
                         font-weight:600;text-align:right;">{v}</td>
            </tr>
            """
            for k, v in stats.items()
        )
        notif_items = "".join(
            f"""
            <div style="background:#f9fafb;border-radius:10px;padding:14px;
                        margin-bottom:10px;border-left:4px solid #FE3C72;">
              <p style="margin:0 0 4px;font-weight:700;color:#111827;font-size:14px;">
                {n.title}
              </p>
              <p style="margin:0;color:#6b7280;font-size:13px;">{n.message}</p>
            </div>
            """
            for n in notifications[:10]
        )
        overflow = (
            f'<p style="color:#9ca3af;font-size:12px;margin:8px 0 0;">... and {len(notifications) - 10} more</p>'
            if len(notifications) > 10
            else ""
        )
        btn = _PINK_BTN.format(
            url="https://vrenum.app/notifications", label="View All Notifications →"
        )
        unsub = _UNSUB.format(link=_unsub_link(unsubscribe_token))
        body = f"""
          <p style="margin:0 0 8px;color:#6b7280;font-size:15px;">{greeting}</p>
          <h2 style="margin:0 0 16px;color:#111827;font-size:22px;font-weight:700;">
            📊 Your Weekly Summary
          </h2>
          <p style="margin:0 0 24px;color:#6b7280;font-size:15px;">
            Here's what happened on Vrenum this week.
          </p>
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="background:#f9fafb;border-radius:12px;
                        overflow:hidden;margin-bottom:24px;">
            {stats_rows}
          </table>
          <h3 style="margin:0 0 16px;color:#111827;font-size:16px;font-weight:700;">
            Recent Notifications
          </h3>
          {notif_items}
          {overflow}
          {btn}
          {unsub}
        """
        return _HEADER + body + _FOOTER
