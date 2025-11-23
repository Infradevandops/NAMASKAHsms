"""Content Security Policy middleware."""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class CSPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # CSP policy to prevent XSS
        csp_policy = (
            "default - src 'sel'; "
            "script - src 'self' 'unsafe - inline' https://cdn.jsdelivr.net; "
            "style - src 'self' 'unsafe - inline' https://fonts.googleapis.com; "
            "font - src 'self' https://fonts.gstatic.com; "
            "img - src 'self' data: https:; "
            "connect - src 'self' https://api.paystack.co; "
            "frame - ancestors 'none';"
        )

        response.headers["Content - Security-Policy"] = csp_policy
        return response
