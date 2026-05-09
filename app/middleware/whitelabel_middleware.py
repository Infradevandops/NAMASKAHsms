"""Whitelabel middleware for domain-based tenant resolution and branding injection"""

import logging
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.database import SessionLocal
from app.services.whitelabel_service import whitelabel_service

logger = logging.getLogger(__name__)


class WhitelabelMiddleware(BaseHTTPMiddleware):
    """
    Middleware to detect custom domains and inject whitelabel branding

    Flow:
    1. Extract domain from request host
    2. Check if it's a custom whitelabel domain
    3. Load branding configuration
    4. Inject into request state
    5. Modify response to include custom CSS
    """

    def __init__(self, app, base_domain: str):
        super().__init__(app)
        self.base_domain = (
            base_domain.replace("http://", "").replace("https://", "").split(":")[0]
        )

    async def dispatch(self, request: Request, call_next):
        """Process request and inject whitelabel branding"""

        # Extract domain from host header
        host = request.headers.get("host", "").split(":")[0]

        # Initialize whitelabel state
        request.state.whitelabel = {
            "enabled": False,
            "partner_id": None,
            "branding": None,
            "domain": host,
        }

        # Check if this is a custom domain (not the platform domain)
        if (
            host
            and host != self.base_domain
            and host != "localhost"
            and host != "127.0.0.1"
        ):
            db = SessionLocal()
            try:
                # Query whitelabel branding by domain
                branding = whitelabel_service.get_branding_by_domain(db, host)

                if branding:
                    # Inject whitelabel state
                    request.state.whitelabel = {
                        "enabled": True,
                        "partner_id": branding.user_id,
                        "branding": branding.to_dict(),
                        "domain": host,
                    }
                    logger.debug(
                        f"Whitelabel enabled for domain: {host}, partner: {branding.user_id}"
                    )
                else:
                    logger.debug(
                        f"No whitelabel configuration found for domain: {host}"
                    )

            except Exception as e:
                logger.error(f"Error loading whitelabel config for {host}: {e}")
            finally:
                db.close()

        # Process request
        response = await call_next(request)

        # Inject custom CSS if whitelabel is enabled and response is HTML
        if request.state.whitelabel["enabled"] and response.headers.get(
            "content-type", ""
        ).startswith("text/html"):
            response = await self._inject_branding_css(request, response)

        return response

    async def _inject_branding_css(
        self, request: Request, response: Response
    ) -> Response:
        """Inject custom CSS variables into HTML response"""
        try:
            branding = request.state.whitelabel.get("branding")
            if not branding:
                return response

            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            # Decode HTML
            html = body.decode("utf-8")

            # Create custom CSS
            custom_css = f"""
<style id="whitelabel-branding">
:root {{
    --primary-color: {branding['primary_color']};
    --secondary-color: {branding['secondary_color']};
    --accent-color: {branding['accent_color']};
    --font-family: {branding['font_family']}, sans-serif;
}}

/* Apply custom colors */
.btn-primary,
.bg-primary {{
    background: linear-gradient(135deg, {branding['primary_color']} 0%, {branding['secondary_color']} 100%) !important;
}}

.text-primary {{
    color: {branding['primary_color']} !important;
}}

.border-primary {{
    border-color: {branding['primary_color']} !important;
}}

/* Custom logo */
.navbar-brand img,
.logo {{
    content: url('{branding['logo_url']}') !important;
}}

/* Custom font */
body {{
    font-family: {branding['font_family']}, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}}
</style>
"""

            # Inject before </head> tag
            if "</head>" in html:
                html = html.replace("</head>", f"{custom_css}\n</head>")
            else:
                # If no </head>, inject at start of body
                html = html.replace("<body>", f"<body>\n{custom_css}")

            # Update response
            from starlette.responses import Response as StarletteResponse

            return StarletteResponse(
                content=html.encode("utf-8"),
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="text/html",
            )

        except Exception as e:
            logger.error(f"Error injecting branding CSS: {e}")
            return response


def get_whitelabel_context(request: Request) -> dict:
    """
    Helper function to get whitelabel context from request

    Usage in templates:
        whitelabel = get_whitelabel_context(request)
        if whitelabel['enabled']:
            company_name = whitelabel['branding']['company_name']
    """
    if hasattr(request.state, "whitelabel"):
        return request.state.whitelabel

    return {"enabled": False, "partner_id": None, "branding": None, "domain": None}
