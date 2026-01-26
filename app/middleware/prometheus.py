"""Prometheus metrics middleware."""

import time

from fastapi import Request
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware

request_count = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])

request_duration = Histogram("http_request_duration_seconds", "HTTP request duration", ["method", "endpoint"])


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
        ).inc()

        request_duration.labels(method=request.method, endpoint=request.url.path).observe(duration)

        return response
