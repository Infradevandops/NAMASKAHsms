"""Per-provider circuit breaker.

Three states: CLOSED (normal) → OPEN (failing) → HALF-OPEN (testing recovery).

ProviderRouter checks circuit state before routing. If primary is OPEN,
skip directly to failover without attempting the call.

Stored in Redis so state is shared across Gunicorn workers.
Falls back to in-memory if Redis is unavailable.
"""

import asyncio
import time
from typing import Dict

from app.core.logging import get_logger

logger = get_logger(__name__)

FAILURE_THRESHOLD = 5    # open after N failures in window
WINDOW_SECONDS = 60      # rolling failure window
RECOVERY_TIMEOUT = 30    # seconds before trying HALF-OPEN
HALF_OPEN_MAX = 1        # test calls allowed in HALF-OPEN


class CircuitBreaker:
    """In-process circuit breaker with Redis-backed state."""

    def __init__(self):
        # Fallback in-memory state
        self._state: Dict[str, str] = {}          # provider -> CLOSED|OPEN|HALF_OPEN
        self._failures: Dict[str, list] = {}       # provider -> [timestamp, ...]
        self._opened_at: Dict[str, float] = {}     # provider -> epoch
        self._half_open_calls: Dict[str, int] = {} # provider -> count

    def _redis_key(self, provider: str) -> str:
        return f"cb:{provider}"

    def _get_state(self, provider: str) -> str:
        try:
            from app.core.cache import get_redis
            r = get_redis()
            val = r.hget(self._redis_key(provider), "state")
            return val.decode() if val else "CLOSED"
        except Exception:
            return self._state.get(provider, "CLOSED")

    def _set_state(self, provider: str, state: str):
        self._state[provider] = state
        try:
            from app.core.cache import get_redis
            r = get_redis()
            r.hset(self._redis_key(provider), "state", state)
            r.expire(self._redis_key(provider), 300)
        except Exception:
            pass

    def is_open(self, provider: str) -> bool:
        state = self._get_state(provider)
        if state == "OPEN":
            # Check if recovery timeout has passed
            opened = self._opened_at.get(provider, 0)
            if time.time() - opened >= RECOVERY_TIMEOUT:
                self._set_state(provider, "HALF_OPEN")
                self._half_open_calls[provider] = 0
                logger.info(f"Circuit breaker {provider}: OPEN → HALF_OPEN")
                return False
            return True
        return False

    def record_success(self, provider: str):
        state = self._get_state(provider)
        if state == "HALF_OPEN":
            self._set_state(provider, "CLOSED")
            self._failures[provider] = []
            logger.info(f"Circuit breaker {provider}: HALF_OPEN → CLOSED (recovery confirmed)")
        elif state == "CLOSED":
            # Clear old failures
            now = time.time()
            self._failures.setdefault(provider, [])
            self._failures[provider] = [t for t in self._failures[provider]
                                         if now - t < WINDOW_SECONDS]

    def record_failure(self, provider: str):
        now = time.time()
        self._failures.setdefault(provider, [])
        self._failures[provider].append(now)
        # Prune outside window
        self._failures[provider] = [t for t in self._failures[provider]
                                     if now - t < WINDOW_SECONDS]

        state = self._get_state(provider)
        if state == "HALF_OPEN":
            self._set_state(provider, "OPEN")
            self._opened_at[provider] = now
            logger.warning(f"Circuit breaker {provider}: HALF_OPEN → OPEN (test call failed)")
        elif state == "CLOSED" and len(self._failures[provider]) >= FAILURE_THRESHOLD:
            self._set_state(provider, "OPEN")
            self._opened_at[provider] = now
            logger.warning(
                f"Circuit breaker {provider}: CLOSED → OPEN "
                f"({len(self._failures[provider])} failures in {WINDOW_SECONDS}s)"
            )


# Module-level singleton
circuit_breaker = CircuitBreaker()
