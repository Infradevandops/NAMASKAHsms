"""
Email preference policy — single authoritative decision point.

All optional email sends MUST call can_send() before dispatching.
Account/security and transactional-essential sends bypass this check.
"""

from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.notification_preference import NotificationPreference
from app.models.user import NotificationSettings, User
from app.services.email_classes import EmailClass, is_suppressible_by_opt_out

logger = get_logger(__name__)

# Categories that map to NotificationSettings legacy fields
_LEGACY_MAP = {
    "sms_received": "email_on_sms",
    "verification_completed": "email_on_sms",
    "low_balance_warning": "email_on_low_balance",
}


class EmailPreferencePolicy:
    """
    Decides whether an optional email may be sent to a user.

    Rules (all must pass for optional_product):
    1. User account is active and not suspended/banned
    2. category preference row exists and enabled=True
    3. 'email' is in delivery_methods
    4. frequency is not 'never'
    5. Legacy NotificationSettings not explicitly disabled (precedence: category row wins
       if it exists; legacy field is fallback for categories without a row)
    """

    def __init__(self, db: Session):
        self.db = db

    def can_send(
        self,
        user_id: str,
        category: str,
        email_class: EmailClass,
    ) -> Tuple[bool, str]:
        """
        Return (allowed: bool, reason: str).

        For non-suppressible classes always returns (True, 'not_optional').
        """
        if not is_suppressible_by_opt_out(email_class):
            return True, "not_optional"

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "user_not_found"
        if not user.is_active or user.is_suspended or user.is_banned:
            return False, "account_inactive"

        pref = (
            self.db.query(NotificationPreference)
            .filter(
                NotificationPreference.user_id == user_id,
                NotificationPreference.notification_type == category,
            )
            .first()
        )

        if pref is not None:
            if not pref.enabled:
                return False, "category_disabled"
            methods = [
                m.strip()
                for m in (pref.delivery_methods or "").split(",")
                if m.strip()
            ]
            if "email" not in methods:
                return False, "email_not_in_delivery_methods"
            if (pref.frequency or "instant") == "never":
                return False, "frequency_never"
            return True, "allowed"

        # No preference row — fall back to legacy NotificationSettings
        legacy_field = _LEGACY_MAP.get(category)
        if legacy_field:
            ns = (
                self.db.query(NotificationSettings)
                .filter(NotificationSettings.user_id == user_id)
                .first()
            )
            if ns and not getattr(ns, legacy_field, True):
                return False, f"legacy_{legacy_field}_disabled"

        # Default: allow (opt-in by default)
        return True, "default_allow"

    def get_effective_preferences(self, user_id: str) -> dict:
        """
        Return computed preference state for all categories.
        Used by GET /api/notifications/email/preferences.
        """
        prefs = (
            self.db.query(NotificationPreference)
            .filter(NotificationPreference.user_id == user_id)
            .all()
        )

        result = {}
        for p in prefs:
            methods = [
                m.strip()
                for m in (p.delivery_methods or "").split(",")
                if m.strip()
            ]
            result[p.notification_type] = {
                "enabled": p.enabled,
                "email_enabled": p.enabled and "email" in methods,
                "frequency": p.frequency or "instant",
            }

        any_email_enabled = (
            any(v["email_enabled"] for v in result.values()) if result else False
        )

        return {
            "email_notifications_enabled": any_email_enabled,
            "notification_types": result,
        }

    def set_email_enabled(
        self,
        user_id: str,
        category: str,
        email_enabled: bool,
        db: Optional[Session] = None,
    ) -> bool:
        """
        Update both delivery_methods AND enabled flag atomically.
        Returns True on success.
        """
        session = db or self.db
        pref = (
            session.query(NotificationPreference)
            .filter(
                NotificationPreference.user_id == user_id,
                NotificationPreference.notification_type == category,
            )
            .first()
        )
        if not pref:
            return False

        methods = [
            m.strip()
            for m in (pref.delivery_methods or "").split(",")
            if m.strip()
        ]
        if email_enabled:
            if "email" not in methods:
                methods.append("email")
            pref.enabled = True
        else:
            methods = [m for m in methods if m != "email"]
            # Only disable the category if no delivery methods remain
            if not methods:
                pref.enabled = False

        pref.delivery_methods = ",".join(methods) if methods else "toast"
        session.commit()
        return True

    def unsubscribe_all_optional(self, user_id: str) -> int:
        """Remove email from all optional category delivery methods. Returns count updated."""
        prefs = (
            self.db.query(NotificationPreference)
            .filter(NotificationPreference.user_id == user_id)
            .all()
        )
        count = 0
        for p in prefs:
            methods = [
                m.strip()
                for m in (p.delivery_methods or "").split(",")
                if m.strip()
            ]
            if "email" in methods:
                methods = [m for m in methods if m != "email"]
                p.delivery_methods = ",".join(methods) if methods else "toast"
                count += 1
        if count:
            self.db.commit()
        return count
