"""Quick smoke checks for the changes made to timeouts, polling, and middleware.
Run: python scripts/smoke_checks.py
"""

import importlib

print('IMPORT CHECK START')
mods = [
    'app.core.config',
    'app.services.textverified_service',
    'app.services.sms_polling_service',
    'app.middleware.rate_limiting',
    'main',
]

for m in mods:
    try:
        mod = importlib.import_module(m)
        print(m, 'OK')
    except Exception as e:
        print(m, 'ERROR', e)

# Check Settings values
try:
    from app.core.config import get_settings
    s = get_settings()
    print('JWT minutes:', s.jwt_expire_minutes)
    print('HTTP timeout:', s.http_timeout_seconds, 'connect', s.http_connect_timeout_seconds, 'read', s.http_read_timeout_seconds)
    print('SMS polling minutes:', s.sms_polling_max_minutes)
except Exception as e:
    print('Settings ERROR', e)

# Instantiate TextVerifiedService
try:
    from app.services.textverified_service import TextVerifiedService
    t = TextVerifiedService()
    print('TextVerified enabled:', t.enabled)
except Exception as e:
    print('TextVerifiedService ERROR', e)

# Instantiate SMSPollingService and compute max attempts
try:
    from app.services.sms_polling_service import SMSPollingService
    sps = SMSPollingService()
    # compute max_attempts using settings
    from app.core.config import get_settings
    settings = get_settings()
    initial_interval = settings.sms_polling_initial_interval_seconds
    max_attempts = int((settings.sms_polling_max_minutes * 60) / max(1, initial_interval))
    print('Computed max_attempts:', max_attempts)
except Exception as e:
    print('SMSPollingService ERROR', e)

# Instantiate RateLimitMiddleware
try:
    from fastapi import FastAPI

    from app.middleware.rate_limiting import RateLimitMiddleware
    app = FastAPI()
    rm = RateLimitMiddleware(app)
    print('RateLimit defaults:', rm.default_requests, rm.default_window)
except Exception as e:
    print('RateLimitMiddleware ERROR', e)

# Create app
try:
    from main import create_app
    app = create_app()
    print('FastAPI app created OK')
except Exception as e:
    print('create_app ERROR', e)

print('IMPORT CHECK END')
