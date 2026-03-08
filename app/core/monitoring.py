"""
Monitoring and observability setup
Lightweight alternative to Datadog
"""
import os
import logging
from typing import Optional

# Sentry for error tracking
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False


def init_monitoring(environment: str = "production"):
    """Initialize monitoring stack"""
    
    # 1. Sentry (Error Tracking)
    if SENTRY_AVAILABLE and os.getenv("SENTRY_DSN"):
        sentry_sdk.init(
            dsn=os.getenv("SENTRY_DSN"),
            environment=environment,
            traces_sample_rate=0.1,  # 10% of transactions
            profiles_sample_rate=0.1,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
            before_send=filter_sensitive_data,
        )
        logging.info("✅ Sentry monitoring initialized")
    
    # 2. Structured logging
    setup_structured_logging()


def filter_sensitive_data(event, hint):
    """Remove sensitive data from Sentry events"""
    if 'request' in event:
        headers = event['request'].get('headers', {})
        headers.pop('Authorization', None)
        headers.pop('Cookie', None)
    return event


def setup_structured_logging():
    """Configure structured logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


# Metrics helpers (simple counters)
class SimpleMetrics:
    """Lightweight metrics tracking"""
    
    @staticmethod
    def track_payment(amount: float, status: str):
        logging.info(f"METRIC: payment amount={amount} status={status}")
    
    @staticmethod
    def track_sms(country: str, service: str, status: str):
        logging.info(f"METRIC: sms country={country} service={service} status={status}")
    
    @staticmethod
    def track_api_call(endpoint: str, duration_ms: float, status_code: int):
        logging.info(f"METRIC: api endpoint={endpoint} duration={duration_ms}ms status={status_code}")


metrics = SimpleMetrics()
