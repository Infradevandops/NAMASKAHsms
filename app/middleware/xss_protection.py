"""XSS protection middleware."""

import json

from starlette.types import ASGIApp, Receive, Scope, Send

from app.utils.sanitization import validate_and_sanitize_response


class XSSProtectionMiddleware:
    """Pure ASGI middleware to prevent XSS attacks by sanitizing JSON responses.

    Uses ASGI directly instead of BaseHTTPMiddleware to avoid the
    Content-Length mismatch bug when stacked with other middleware.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        initial_message: dict = {}
        body_chunks: list[bytes] = []
        is_json = False

        async def send_wrapper(message: dict) -> None:
            nonlocal initial_message, is_json

            if message["type"] == "http.response.start":
                headers = dict(
                    (k.lower(), v)
                    for k, v in (
                        (k.decode(), v.decode())
                        for k, v in message.get("headers", [])
                    )
                )
                is_json = headers.get("content-type", "").startswith("application/json")
                if is_json:
                    initial_message = message
                    return
                await send(message)
                return

            if message["type"] == "http.response.body":
                if not is_json:
                    await send(message)
                    return

                body_chunks.append(message.get("body", b""))
                more = message.get("more_body", False)
                if more:
                    return

                full_body = b"".join(body_chunks)
                if full_body:
                    try:
                        data = json.loads(full_body)
                        sanitized = validate_and_sanitize_response(data)
                        full_body = json.dumps(sanitized).encode()
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass

                # Rebuild headers with correct content-length
                raw_headers = [
                    (k, v)
                    for k, v in initial_message.get("headers", [])
                    if k.lower() != b"content-length"
                ]
                raw_headers.append(
                    (b"content-length", str(len(full_body)).encode())
                )
                initial_message["headers"] = raw_headers

                await send(initial_message)
                await send({"type": "http.response.body", "body": full_body})
                return

        await self.app(scope, receive, send_wrapper)
