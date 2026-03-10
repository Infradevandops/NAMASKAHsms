"""API documentation configuration for task 14.1."""


from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def custom_openapi(app: FastAPI):

    """Generate custom OpenAPI schema with comprehensive documentation."""
if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Namaskah SMS API",
        version="2.3.0",
        description="""
        ## Namaskah SMS Verification Platform

        A comprehensive SMS verification service supporting 1,800+ services worldwide.

        ### Features
        - SMS/Voice verification for popular services
        - Secure payment processing via Paystack
        - Real-time verification status tracking
        - Admin dashboard and analytics
        - API key authentication for developers

        ### Authentication
        - **JWT Bearer Token**: For user authentication
        - **API Key**: For programmatic access (Header: `X-API-Key`)

        ### Rate Limits
        - **Default**: 60 requests per minute
        - **Payment endpoints**: 10 requests per minute
        - **Admin endpoints**: 100 requests per minute

        ### Error Handling
        All errors follow RFC 7807 Problem Details format:
        ```json
        {
            "error": "Error description",
            "code": "ERROR_CODE",
            "details": {}
        }
        ```
        """,
        routes=app.routes,
    )

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
        "ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-API-Key"},
    }

    # Add examples for common responses
    openapi_schema["components"]["examples"] = {
        "SuccessResponse": {
            "summary": "Success Response",
            "value": {"success": True, "message": "Operation completed"},
        },
        "ErrorResponse": {
            "summary": "Error Response",
            "value": {"error": "Invalid input", "code": "VALIDATION_ERROR"},
        },
        "ValidationError": {
            "summary": "Validation Error",
            "value": {
                "error": "Validation failed",
                "code": "VALIDATION_ERROR",
                "details": {"field": "email", "message": "Invalid email format"},
            },
        },
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# API documentation metadata
tags_metadata = [
    {
        "name": "Authentication",
        "description": "User registration, login, and API key management",
        "externalDocs": {
            "description": "Authentication Guide",
            "url": "https://docs.namaskah.app/auth",
        },
    },
    {
        "name": "Verification",
        "description": "SMS/Voice verification operations",
        "externalDocs": {
            "description": "Verification Guide",
            "url": "https://docs.namaskah.app/verification",
        },
    },
    {
        "name": "Wallet",
        "description": "Payment processing and wallet management",
        "externalDocs": {
            "description": "Payment Guide",
            "url": "https://docs.namaskah.app/payments",
        },
    },
    {
        "name": "Admin",
        "description": "Administrative operations (admin access required)",
    },
    {"name": "System", "description": "System health and configuration endpoints"},
]
