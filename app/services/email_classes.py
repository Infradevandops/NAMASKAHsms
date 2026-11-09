"""Email message classification — single source of truth for all send paths."""

from enum import Enum
from typing import Dict


class EmailClass(str, Enum):
    """
    Every outbound email must be assigned one of these classes before sending.

    Policy summary
    --------------
    account_security        — never suppressed by optional opt-outs; abuse/token controls apply
    transactional_essential — never suppressed by marketing opt-out; deduplicate by event key
    optional_product        — requires category enabled + email in delivery_methods + frequency ok
    user_configured_forwarding — requires forwarding feature enabled + valid destination
    operational_admin       — uses configured operational recipients; ignores end-user prefs
    user_initiated_test     — explicitly requested diagnostic; rate-limit and audit
    """

    ACCOUNT_SECURITY = "account_security"
    TRANSACTIONAL_ESSENTIAL = "transactional_essential"
    OPTIONAL_PRODUCT = "optional_product"
    USER_CONFIGURED_FORWARDING = "user_configured_forwarding"
    OPERATIONAL_ADMIN = "operational_admin"
    USER_INITIATED_TEST = "user_initiated_test"


# Maps every template key / method name to its class.
# Update this whenever a new template is added.
TEMPLATE_CLASS_MAP: Dict[str, EmailClass] = {
    # Transactional — email_service.py
    "send_payment_receipt": EmailClass.TRANSACTIONAL_ESSENTIAL,
    "send_payment_failed_alert": EmailClass.TRANSACTIONAL_ESSENTIAL,
    "send_refund_notification": EmailClass.TRANSACTIONAL_ESSENTIAL,
    "send_verification_email": EmailClass.ACCOUNT_SECURITY,
    "send_password_reset": EmailClass.ACCOUNT_SECURITY,
    "send_welcome_email": EmailClass.OPTIONAL_PRODUCT,
    "send_tier_upgrade_email": EmailClass.TRANSACTIONAL_ESSENTIAL,
    # Notification — email_service.py
    "send_notification_email": EmailClass.OPTIONAL_PRODUCT,
    "send_verification_initiated_email": EmailClass.OPTIONAL_PRODUCT,
    "send_verification_completed_email": EmailClass.OPTIONAL_PRODUCT,
    "send_low_balance_alert_email": EmailClass.OPTIONAL_PRODUCT,
    "send_daily_digest_email": EmailClass.OPTIONAL_PRODUCT,
    "send_weekly_digest_email": EmailClass.OPTIONAL_PRODUCT,
    # Whitelabel template types — email_template_service.py
    "welcome": EmailClass.OPTIONAL_PRODUCT,
    "verification_code": EmailClass.ACCOUNT_SECURITY,
    "payment_success": EmailClass.TRANSACTIONAL_ESSENTIAL,
    "payment_failed": EmailClass.TRANSACTIONAL_ESSENTIAL,
    "low_balance": EmailClass.OPTIONAL_PRODUCT,
    "tier_upgrade": EmailClass.TRANSACTIONAL_ESSENTIAL,
    "password_reset": EmailClass.ACCOUNT_SECURITY,
    # Contact forwarding
    "contact_forwarding": EmailClass.OPERATIONAL_ADMIN,
    # Test send
    "test_email": EmailClass.USER_INITIATED_TEST,
}


def get_template_class(template_key: str) -> EmailClass:
    """Return the EmailClass for a template key, defaulting to optional_product."""
    return TEMPLATE_CLASS_MAP.get(template_key, EmailClass.OPTIONAL_PRODUCT)


def is_suppressible_by_opt_out(email_class: EmailClass) -> bool:
    """Return True if this class can be suppressed by an optional email opt-out."""
    return email_class in (
        EmailClass.OPTIONAL_PRODUCT,
        EmailClass.USER_CONFIGURED_FORWARDING,
    )
