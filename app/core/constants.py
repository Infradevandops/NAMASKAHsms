"""Application constants and configuration values."""

# CSRF Protection
CSRF_TOKEN_LENGTH = 32
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_FORM_FIELD = "csrf_token"

# Security Headers
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosni",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'sel'; script-src 'sel' 'unsafe-inline'; style-src 'sel' 'unsafe-inline'",
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