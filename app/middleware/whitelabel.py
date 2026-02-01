"""White - label middleware for dynamic branding."""


from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.whitelabel_service import whitelabel_service

class WhiteLabelMiddleware(BaseHTTPMiddleware):

    """Middleware to inject white - label configuration."""

    async def dispatch(self, request: Request, call_next):
try:
            # Get domain from request
            domain = request.headers.get("host", "").split(":")[0]

            # Get white - label config
            config = await whitelabel_service.get_config_by_domain(domain)

            # Inject config into request state
            request.state.whitelabel_config = config
except Exception:
            # Continue without whitelabel config if error
            request.state.whitelabel_config = None

        response = await call_next(request)

        # Add custom headers if white - labeled
if hasattr(request.state, "whitelabel_config") and request.state.whitelabel_config:
            response.headers["X - Whitelabel"] = "true"
            response.headers["X - Brand"] = request.state.whitelabel_config.get("company_name", "")

        return response