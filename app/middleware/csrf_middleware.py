"""CSRF protection middleware."""


import secrets
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class CSRFMiddleware(BaseHTTPMiddleware):

    """CSRF token validation middleware."""

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
    CSRF_HEADER = "X-CSRF-Token"
    CSRF_COOKIE = "csrf_token"

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip CSRF for public endpoints
        if self._is_public_endpoint(request.url.path):
        return await call_next(request)

        # Generate CSRF token for GET requests
        if request.method in self.SAFE_METHODS:
            response = await call_next(request)
            csrf_token = secrets.token_urlsafe(32)
            response.set_cookie(
                self.CSRF_COOKIE,
                csrf_token,
                httponly=False,
                secure=True,
                samesite="strict",
                max_age=3600,
            )
            response.headers["X-CSRF-Token"] = csrf_token
        return response

        # Validate CSRF token for state-changing requests
        if request.method in {"POST", "PUT", "DELETE", "PATCH"}:
            token_from_header = request.headers.get(self.CSRF_HEADER)
            token_from_cookie = request.cookies.get(self.CSRF_COOKIE)

        if not token_from_header or not token_from_cookie:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token missing")

        if token_from_header != token_from_cookie:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token invalid")

        return await call_next(request)

    def _is_public_endpoint(self, path: str) -> bool:

        """Check if endpoint is public (no CSRF required)."""
        public_paths = [
            "/",
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/google",
            "/api/auth/forgot-password",
            "/api/auth/reset-password",
            "/api/auth/verify-email",
            "/api/auth/refresh",
            "/api/auth/logout",
            "/api/auth/logout-all",
            "/api/countries",
            "/api/system/health",
            "/static/",
            "/auth/",
        ]
        return any(path.startswith(p) for p in public_paths)