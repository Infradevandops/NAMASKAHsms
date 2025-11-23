"""Enhanced error handling middleware for graceful error responses."""
import logging
from typing import Callable

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware to handle errors gracefully and provide consistent error responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except HTTPException:
            # Re - raise HTTP exceptions to be handled by FastAPI
            raise
        except Exception as exc:
            # Log the error
            logger.error(
                "Unhandled error in %s %s: %s",
                request.method,
                request.url,
                str(exc),
                exc_info=True,
            )

            # Return a graceful error response
            return await self.handle_error(request, exc)

    async def handle_error(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle different types of errors and return appropriate responses."""

        # Database connection errors
        if "database" in str(exc).lower() or "connection" in str(exc).lower():
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Service temporarily unavailable",
                    "message": "Database connection issue. Please try again later.",
                    "fallback_available": True,
                },
            )

        # Network/API errors
        if "network" in str(exc).lower() or "timeout" in str(exc).lower():
            return JSONResponse(
                status_code=503,
                content={
                    "error": "External service unavailable",
                    "message": "External API is temporarily unavailable. Using fallback data.",
                    "fallback_available": True,
                },
            )

        # Authentication errors
        if "auth" in str(exc).lower() or "token" in str(exc).lower():
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Authentication required",
                    "message": "Please login to continue.",
                    "redirect": "/auth/login",
                },
            )

        # Permission errors
        if "permission" in str(exc).lower() or "forbidden" in str(exc).lower():
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Access denied",
                    "message": "You don't have permission to access this resource.",
                },
            )

        # Validation errors
        if "validation" in str(exc).lower() or "invalid" in str(exc).lower():
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Invalid request",
                    "message": "Please check your input and try again.",
                },
            )

        # Generic server error
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "message": "Something went wrong. Please try again later.",
                "support_contact": "support@namaskahsms.com",
            },
        )


class APIFallbackMiddleware(BaseHTTPMiddleware):
    """Middleware to provide fallback responses for critical API endpoints."""

    FALLBACK_RESPONSES = {
        "/verify/services": {
            "services": [
                {
                    "id": "telegram",
                    "name": "telegram",
                    "display_name": "Telegram",
                    "price": 0.75,
                    "available": True,
                },
                {
                    "id": "whatsapp",
                    "name": "whatsapp",
                    "display_name": "WhatsApp",
                    "price": 0.75,
                    "available": True,
                },
                {
                    "id": "discord",
                    "name": "discord",
                    "display_name": "Discord",
                    "price": 0.75,
                    "available": True,
                },
                {
                    "id": "google",
                    "name": "google",
                    "display_name": "Google",
                    "price": 0.75,
                    "available": True,
                },
                {
                    "id": "instagram",
                    "name": "instagram",
                    "display_name": "Instagram",
                    "price": 1.00,
                    "available": True,
                },
                {
                    "id": "facebook",
                    "name": "facebook",
                    "display_name": "Facebook",
                    "price": 1.00,
                    "available": True,
                },
                {
                    "id": "twitter",
                    "name": "twitter",
                    "display_name": "Twitter",
                    "price": 1.00,
                    "available": True,
                },
                {
                    "id": "tiktok",
                    "name": "tiktok",
                    "display_name": "TikTok",
                    "price": 1.00,
                    "available": True,
                },
            ]
        },
        "/verify/services/list": {
            "categories": {
                "Social": [
                    "telegram",
                    "whatsapp",
                    "discord",
                    "instagram",
                    "facebook",
                    "twitter",
                    "tiktok",
                ],
                "Finance": ["paypal", "cashapp", "venmo", "coinbase"],
                "Shopping": ["amazon", "ebay", "etsy"],
                "Gaming": ["steam", "epic", "xbox"],
                "Other": ["google", "microsoft", "apple", "uber"],
            },
            "tiers": {
                "tier1": {
                    "name": "High - Demand",
                    "price": 0.75,
                    "services": ["whatsapp", "telegram", "discord", "google"],
                },
                "tier2": {
                    "name": "Standard",
                    "price": 1.0,
                    "services": ["instagram", "facebook", "twitter", "tiktok"],
                },
                "tier3": {"name": "Premium", "price": 1.5, "services": ["paypal"]},
                "tier4": {"name": "Specialty", "price": 2.0, "services": []},
            },
        },
        "/countries/": {
            "countries": [
                {
                    "code": "US",
                    "name": "United States",
                    "price_multiplier": 1.0,
                    "voice_supported": True,
                    "region": "North America",
                    "tier": "Standard",
                },
                {
                    "code": "GB",
                    "name": "United Kingdom",
                    "price_multiplier": 1.0,
                    "voice_supported": True,
                    "region": "Europe",
                    "tier": "Standard",
                },
                {
                    "code": "CA",
                    "name": "Canada",
                    "price_multiplier": 1.1,
                    "voice_supported": True,
                    "region": "North America",
                    "tier": "Standard",
                },
                {
                    "code": "DE",
                    "name": "Germany",
                    "price_multiplier": 1.0,
                    "voice_supported": True,
                    "region": "Europe",
                    "tier": "Standard",
                },
                {
                    "code": "FR",
                    "name": "France",
                    "price_multiplier": 1.0,
                    "voice_supported": True,
                    "region": "Europe",
                    "tier": "Standard",
                },
                {
                    "code": "AU",
                    "name": "Australia",
                    "price_multiplier": 1.4,
                    "voice_supported": True,
                    "region": "Asia - Pacific",
                    "tier": "Premium",
                },
                {
                    "code": "JP",
                    "name": "Japan",
                    "price_multiplier": 1.5,
                    "voice_supported": True,
                    "region": "Asia - Pacific",
                    "tier": "Premium",
                },
                {
                    "code": "IN",
                    "name": "India",
                    "price_multiplier": 0.2,
                    "voice_supported": False,
                    "region": "Asia - Pacific",
                    "tier": "Economy",
                },
                {
                    "code": "BR",
                    "name": "Brazil",
                    "price_multiplier": 0.4,
                    "voice_supported": True,
                    "region": "Latin America",
                    "tier": "Economy",
                },
                {
                    "code": "MX",
                    "name": "Mexico",
                    "price_multiplier": 0.4,
                    "voice_supported": False,
                    "region": "North America",
                    "tier": "Economy",
                },
            ],
            "total_count": 10,
        },
        "/admin/stats": {
            "total_users": 1,
            "new_users": 0,
            "total_verifications": 0,
            "success_rate": 0.0,
            "total_spent": 0.0,
            "pending_verifications": 0,
        },
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)

            # If response is successful, return it
            if response.status_code < 400:
                return response

            # Check if we have a fallback for this endpoint
            path = str(request.url.path)
            if path in self.FALLBACK_RESPONSES:
                logger.warning("Using fallback response for %s", path)
                return JSONResponse(
                    status_code=200,
                    content=self.FALLBACK_RESPONSES[path],
                    headers={"X - Fallback-Response": "true"},
                )

            return response

        except Exception as exc:
            # Check if we have a fallback for this endpoint
            path = str(request.url.path)
            if path in self.FALLBACK_RESPONSES:
                logger.warning(
                    "Exception occurred, using fallback response for %s: %s",
                    path,
                    str(exc),
                )
                return JSONResponse(
                    status_code=200,
                    content=self.FALLBACK_RESPONSES[path],
                    headers={
                        "X - Fallback-Response": "true",
                        "X - Fallback-Reason": "exception",
                    },
                )

            # Re - raise if no fallback available
            raise exc


def setup_error_handling(app):
    """Setup error handling middleware for the FastAPI app."""
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(APIFallbackMiddleware)

    # Add custom exception handlers
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        return JSONResponse(
            status_code=404,
            content={
                "error": "Not found",
                "message": "The requested resource was not found.",
                "path": str(request.url.path),
            },
        )

    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc):
        logger.error("Internal server error: %s", str(exc), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "Something went wrong on our end. Please try again later.",
            },
        )
