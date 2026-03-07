"""XSS protection middleware."""


import json
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.sanitization import validate_and_sanitize_response


class XSSProtectionMiddleware(BaseHTTPMiddleware):
    """Middleware to prevent XSS attacks by sanitizing responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Only process JSON responses
        if response.headers.get("content-type", "").startswith("application/json"):
            try:
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk

                if body:
                    data = json.loads(body.decode())
                    sanitized_data = validate_and_sanitize_response(data)
                    sanitized_body = json.dumps(sanitized_data).encode()

                    new_headers = dict(response.headers)
                    new_headers.pop("content-length", None)
                    return Response(
                        content=sanitized_body,
                        status_code=response.status_code,
                        headers=new_headers,
                        media_type="application/json",
                    )
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

        return response
