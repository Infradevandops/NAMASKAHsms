"""Financial and verification failure constants."""


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


# User-friendly messages for failure reasons
FAILURE_MESSAGES = {
    # User Actions
    FailureReason.USER_CANCELLED: {
        "label": "User Cancelled",
        "message": "You cancelled this verification",
        "refundable": True,
    },
    FailureReason.USER_TIMEOUT: {
        "label": "User Timeout",
        "message": "Verification expired - you didn't check for the code in time",
        "refundable": True,
    },
    # Provider Issues
    FailureReason.NUMBER_UNAVAILABLE: {
        "label": "Number Unavailable",
        "message": "No phone numbers available for your selected area code. Try a different area code or remove the filter.",
        "refundable": True,
    },
    FailureReason.PROVIDER_API_ERROR: {
        "label": "Provider Error",
        "message": "Our SMS provider is experiencing issues. Please try again in a few minutes.",
        "refundable": True,
    },
    FailureReason.PROVIDER_TIMEOUT: {
        "label": "Provider Timeout",
        "message": "SMS provider took too long to respond. Your payment has been refunded.",
        "refundable": True,
    },
    FailureReason.SMS_NOT_DELIVERED: {
        "label": "SMS Not Delivered",
        "message": "SMS code was not delivered within 10 minutes. Your payment has been refunded.",
        "refundable": True,
    },
    # System Validation
    FailureReason.VOIP_REJECTED: {
        "label": "VOIP Rejected",
        "message": "The assigned number was VOIP/Landline (not mobile). Your payment has been refunded. Try again for a mobile number.",
        "refundable": True,
    },
    FailureReason.CARRIER_MISMATCH: {
        "label": "Carrier Mismatch",
        "message": "Could not find a number matching your carrier preference. Your payment has been refunded.",
        "refundable": True,
    },
    FailureReason.AREA_CODE_UNAVAILABLE: {
        "label": "Area Code Unavailable",
        "message": "No numbers available in your requested area code after 3 attempts. Your payment has been refunded.",
        "refundable": True,
    },
    FailureReason.RETRY_EXHAUSTED: {
        "label": "Retry Exhausted",
        "message": "Maximum retry attempts reached (3/3). Your payment has been refunded.",
        "refundable": True,
    },
    # Payment Issues
    FailureReason.INSUFFICIENT_BALANCE: {
        "label": "Insufficient Balance",
        "message": "Insufficient balance. Please add credits to your wallet.",
        "refundable": False,
    },
    FailureReason.PAYMENT_FAILED: {
        "label": "Payment Failed",
        "message": "Payment processing failed. Please try again.",
        "refundable": False,
    },
    # Internal Errors
    FailureReason.INTERNAL_ERROR: {
        "label": "Internal Error",
        "message": "An internal error occurred. Our team has been notified. Your payment has been refunded.",
        "refundable": True,
    },
    FailureReason.DATABASE_ERROR: {
        "label": "Database Error",
        "message": "A database error occurred. Please try again.",
        "refundable": True,
    },
    FailureReason.CONFIGURATION_ERROR: {
        "label": "Configuration Error",
        "message": "System configuration error. Please contact support.",
        "refundable": True,
    },
}


def format_failure_message(failure_reason: str, error_message: str = None) -> str:
    """Get user-friendly failure message."""
    if not failure_reason:
        return error_message or "Verification failed"

    msg_data = FAILURE_MESSAGES.get(failure_reason)
    if msg_data:
        return msg_data.get("message", error_message or "Verification failed")

    return error_message or "Verification failed"


def format_failure_reason_label(reason_code: str) -> str:
    """Get display label for failure reason."""
    msg_data = FAILURE_MESSAGES.get(reason_code)
    if msg_data:
        return msg_data.get("label")
    return reason_code.replace("_", " ").title() if reason_code else "Unknown"


def format_category_label(category_code: str) -> str:
    """Get display label for failure category."""
    labels = {
        FailureCategory.USER_ACTION: "User Action",
        FailureCategory.PROVIDER_ISSUE: "Provider Issue",
        FailureCategory.SYSTEM_VALIDATION: "System Validation",
        FailureCategory.PAYMENT_ISSUE: "Payment Issue",
        FailureCategory.INTERNAL_ERROR: "Internal Error",
    }
    return labels.get(
        category_code,
        category_code.replace("_", " ").title() if category_code else "Unknown",
    )
