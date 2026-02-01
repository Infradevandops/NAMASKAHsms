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
if response.headers.get("content - type", "").startswith("application/json"):
try:
                # Get response body
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk

                # Parse and sanitize JSON
if body:
                    data = json.loads(body.decode())
                    sanitized_data = validate_and_sanitize_response(data)
                    sanitized_body = json.dumps(sanitized_data).encode()

                    # Create new response with sanitized content
                    return Response(
                        content=sanitized_body,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        media_type="application/json",
                    )
except (json.JSONDecodeError, UnicodeDecodeError):
                # If we can't parse JSON, return original response
                pass

        return response