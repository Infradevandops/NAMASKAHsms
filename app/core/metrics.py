"""Prometheus metrics for performance monitoring.

Tracks:
- Tier identification latency
- Cache hit rates
- API response times
- Error rates
- Request throughput
"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
import time
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Create registry
registry = CollectorRegistry()

# ============================================================================
# TIER IDENTIFICATION METRICS
# ============================================================================

tier_identification_latency = Histogram(
    'tier_identification_latency_seconds',
    'Tier identification latency in seconds',
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0),
    registry=registry
)

tier_identification_errors = Counter(
    'tier_identification_errors_total',
    'Total tier identification errors',
    ['error_type'],
    registry=registry
)

tier_identification_cache_hits = Counter(
    'tier_identification_cache_hits_total',
    'Total tier identification cache hits',
    registry=registry
)

tier_identification_cache_misses = Counter(
    'tier_identification_cache_misses_total',
    'Total tier identification cache misses',
    registry=registry
)

# ============================================================================
# CACHE METRICS
# ============================================================================

cache_hit_rate = Gauge(
    'cache_hit_rate',
    'Cache hit rate (0-1)',
    registry=registry
)

cache_size_bytes = Gauge(
    'cache_size_bytes',
    'Cache size in bytes',
    registry=registry
)

cache_evictions = Counter(
    'cache_evictions_total',
    'Total cache evictions',
    registry=registry
)

# ============================================================================
# API METRICS
# ============================================================================

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0),
    registry=registry
)

api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

api_errors_total = Counter(
    'api_errors_total',
    'Total API errors',
    ['method', 'endpoint', 'error_type'],
    registry=registry
)

# ============================================================================
# FEATURE ACCESS METRICS
# ============================================================================

feature_access_allowed = Counter(
    'feature_access_allowed_total',
    'Total allowed feature accesses',
    ['feature', 'tier'],
    registry=registry
)

feature_access_denied = Counter(
    'feature_access_denied_total',
    'Total denied feature accesses',
    ['feature', 'tier'],
    registry=registry
)

# ============================================================================
# TIER CHANGE METRICS
# ============================================================================

tier_changes = Counter(
    'tier_changes_total',
    'Total tier changes',
    ['old_tier', 'new_tier'],
    registry=registry
)

# ============================================================================
# ERROR METRICS
# ============================================================================

errors_total = Counter(
    'errors_total',
    'Total errors',
    ['error_type', 'severity'],
    registry=registry
)

unauthorized_access_attempts = Counter(
    'unauthorized_access_attempts_total',
    'Total unauthorized access attempts',
    ['feature', 'tier'],
    registry=registry
)

# ============================================================================
# PERFORMANCE METRICS
# ============================================================================

active_requests = Gauge(
    'active_requests',
    'Number of active requests',
    registry=registry
)

request_queue_length = Gauge(
    'request_queue_length',
    'Request queue length',
    registry=registry
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def track_tier_identification(func):
    """Decorator to track tier identification metrics."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            tier_identification_latency.observe(duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            tier_identification_latency.observe(duration)
            tier_identification_errors.labels(error_type=type(e).__name__).inc()
            raise
    return wrapper


def track_cache_hit(hit: bool):
    """Track cache hit or miss."""
    if hit:
        tier_identification_cache_hits.inc()
    else:
        tier_identification_cache_misses.inc()


def track_feature_access(feature: str, tier: str, allowed: bool):
    """Track feature access attempt."""
    if allowed:
        feature_access_allowed.labels(feature=feature, tier=tier).inc()
    else:
        feature_access_denied.labels(feature=feature, tier=tier).inc()
        unauthorized_access_attempts.labels(feature=feature, tier=tier).inc()


def track_tier_change(old_tier: str, new_tier: str):
    """Track tier change."""
    tier_changes.labels(old_tier=old_tier, new_tier=new_tier).inc()


def track_api_request(method: str, endpoint: str, status: int, duration: float):
    """Track API request."""
    api_request_duration.labels(method=method, endpoint=endpoint).observe(duration)
    api_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()


def track_error(error_type: str, severity: str = "error"):
    """Track error."""
    errors_total.labels(error_type=error_type, severity=severity).inc()


def update_cache_hit_rate(hits: int, total: int):
    """Update cache hit rate."""
    if total > 0:
        cache_hit_rate.set(hits / total)


def update_cache_size(size_bytes: int):
    """Update cache size."""
    cache_size_bytes.set(size_bytes)


def increment_cache_evictions():
    """Increment cache evictions."""
    cache_evictions.inc()


def set_active_requests(count: int):
    """Set active request count."""
    active_requests.set(count)


def set_request_queue_length(length: int):
    """Set request queue length."""
    request_queue_length.set(length)
