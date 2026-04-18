"""Application constants and configuration values."""

# CSRF Protection
CSRF_TOKEN_LENGTH = 32
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_FORM_FIELD = "csrf_token"

# Security Headers
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdn.jsdelivr.net https://unpkg.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:;",
}

# Rate Limiting
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 3600

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Verification
VERIFICATION_TIMEOUT_MINUTES = 20
VERIFICATION_COST = 0.50

# Credits
MIN_CREDIT_AMOUNT = 5.0
MAX_CREDIT_AMOUNT = 10000.0
CREDIT_BONUS_THRESHOLDS = {
    50: 7,
    25: 3,
    10: 1,
}

# Password
MIN_PASSWORD_LENGTH = 6
MAX_PASSWORD_LENGTH = 128

# Email
EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS = 24
PASSWORD_RESET_TOKEN_EXPIRY_HOURS = 1

# API Keys
API_KEY_PREFIX = "nsk_"
API_KEY_LENGTH = 32

# Referral
REFERRAL_BONUS_VERIFICATIONS = 2.0
REFERRAL_CODE_LENGTH = 6

# Session
SESSION_TIMEOUT_MINUTES = 30
REFRESH_TOKEN_EXPIRY_DAYS = 7
ACCESS_TOKEN_EXPIRY_HOURS = 24


class FailureReason:
    """Detailed failure reasons for verifications."""

    # User Actions
    USER_CANCELLED = "user_cancelled"
    USER_TIMEOUT = "user_timeout"

    # Provider Issues
    NUMBER_UNAVAILABLE = "number_unavailable"
    PROVIDER_API_ERROR = "provider_api_error"
    PROVIDER_TIMEOUT = "provider_timeout"
    SMS_NOT_DELIVERED = "sms_not_delivered"

    # System Validation
    VOIP_REJECTED = "voip_rejected"
    CARRIER_MISMATCH = "carrier_mismatch"
    AREA_CODE_UNAVAILABLE = "area_code_unavailable"
    RETRY_EXHAUSTED = "retry_exhausted"

    # Payment Issues
    INSUFFICIENT_BALANCE = "insufficient_balance"
    PAYMENT_FAILED = "payment_failed"

    # Internal Errors
    INTERNAL_ERROR = "internal_error"
    DATABASE_ERROR = "database_error"
    CONFIGURATION_ERROR = "configuration_error"

    ALL = [
        USER_CANCELLED,
        USER_TIMEOUT,
        NUMBER_UNAVAILABLE,
        PROVIDER_API_ERROR,
        PROVIDER_TIMEOUT,
        SMS_NOT_DELIVERED,
        VOIP_REJECTED,
        CARRIER_MISMATCH,
        AREA_CODE_UNAVAILABLE,
        RETRY_EXHAUSTED,
        INSUFFICIENT_BALANCE,
        PAYMENT_FAILED,
        INTERNAL_ERROR,
        DATABASE_ERROR,
        CONFIGURATION_ERROR,
    ]


class FailureCategory:
    """High-level failure categories."""

    USER_ACTION = "user_action"
    PROVIDER_ISSUE = "provider_issue"
    SYSTEM_VALIDATION = "system_validation"
    PAYMENT_ISSUE = "payment_issue"
    INTERNAL_ERROR = "internal_error"


# Mapping of reason to category
REASON_TO_CATEGORY = {
    FailureReason.USER_CANCELLED: FailureCategory.USER_ACTION,
    FailureReason.USER_TIMEOUT: FailureCategory.USER_ACTION,
    FailureReason.NUMBER_UNAVAILABLE: FailureCategory.PROVIDER_ISSUE,
    FailureReason.PROVIDER_API_ERROR: FailureCategory.PROVIDER_ISSUE,
    FailureReason.PROVIDER_TIMEOUT: FailureCategory.PROVIDER_ISSUE,
    FailureReason.SMS_NOT_DELIVERED: FailureCategory.PROVIDER_ISSUE,
    FailureReason.VOIP_REJECTED: FailureCategory.SYSTEM_VALIDATION,
    FailureReason.CARRIER_MISMATCH: FailureCategory.SYSTEM_VALIDATION,
    FailureReason.AREA_CODE_UNAVAILABLE: FailureCategory.SYSTEM_VALIDATION,
    FailureReason.RETRY_EXHAUSTED: FailureCategory.SYSTEM_VALIDATION,
    FailureReason.INSUFFICIENT_BALANCE: FailureCategory.PAYMENT_ISSUE,
    FailureReason.PAYMENT_FAILED: FailureCategory.PAYMENT_ISSUE,
    FailureReason.INTERNAL_ERROR: FailureCategory.INTERNAL_ERROR,
    FailureReason.DATABASE_ERROR: FailureCategory.INTERNAL_ERROR,
    FailureReason.CONFIGURATION_ERROR: FailureCategory.INTERNAL_ERROR,
}


class TransactionType:
    """Balance transaction types."""

    DEBIT = "debit"
    REFUND = "refund"
    CREDIT = "credit"
    ADJUSTMENT = "adjustment"
